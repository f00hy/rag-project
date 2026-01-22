# Reference: https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

# Build stage
FROM ghcr.io/astral-sh/uv:0.9-python3.12-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEFAULT_GROUPS=true
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# Runtime stage
FROM python:3.12-slim-trixie

RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER nonroot

EXPOSE 8000

WORKDIR /app

CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "app/main.py"]
