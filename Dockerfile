# Reference: https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

# Build stage
FROM dhi.io/python:3.12-debian13-dev AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEFAULT_GROUPS=true
ENV UV_PYTHON_DOWNLOADS=0
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH=/app/.venv/bin:$PATH
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright
ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed
ENV HF_HOME=/app/.cache/huggingface

RUN playwright install --with-deps chromium

RUN python -c "\
from fastembed import TextEmbedding, SparseTextEmbedding;\
from fastembed.rerank.cross_encoder import TextCrossEncoder;\
from tokenizers import Tokenizer;\
TextEmbedding('BAAI/bge-base-en-v1.5');\
SparseTextEmbedding('prithivida/Splade_PP_en_v1');\
TextCrossEncoder('jinaai/jina-reranker-v1-turbo-en');\
Tokenizer.from_pretrained('prithivida/Splade_PP_en_v1')"


# Runtime stage
FROM dhi.io/python:3.12-debian13

COPY --from=builder --chown=nonroot:nonroot /app /app
COPY --from=builder /usr/lib/ /usr/lib/
COPY --from=builder /usr/share/fonts/ /usr/share/fonts/
COPY --from=builder /etc/fonts/ /etc/fonts/

ENV PYTHONUNBUFFERED=1
ENV PATH=/app/.venv/bin:$PATH
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright
ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed
ENV HF_HOME=/app/.cache/huggingface

USER nonroot

EXPOSE 8000

WORKDIR /app

CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "app/main.py"]
