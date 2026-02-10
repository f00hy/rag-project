"""Text chunking service using hierarchical parent-child chunks with context overlap."""

from chonkie import RecursiveChunker, OverlapRefinery
from tokenizers import Tokenizer
from app.models import Chunk
from app.config import (
    SPARSE_MODEL_NAME,
    PARENT_CHUNK_SIZE,
    CHILD_CHUNK_SIZE,
    OVERLAP_CONTEXT_SIZE,
)

_tokenizer = Tokenizer.from_pretrained(SPARSE_MODEL_NAME)

_parent_chunker = RecursiveChunker.from_recipe(
    name="markdown",
    lang="en",
    tokenizer=_tokenizer,
    chunk_size=PARENT_CHUNK_SIZE,
    min_characters_per_chunk=12,
)

_child_chunker = RecursiveChunker.from_recipe(
    name="markdown",
    lang="en",
    tokenizer=_tokenizer,
    chunk_size=CHILD_CHUNK_SIZE,
    min_characters_per_chunk=12,
)

_prefix_overlapper = OverlapRefinery(
    tokenizer=_tokenizer,
    context_size=OVERLAP_CONTEXT_SIZE,
    mode="token",
    method="prefix",
    merge=False,
    inplace=False,
)

_suffix_overlapper = OverlapRefinery(
    tokenizer=_tokenizer,
    context_size=OVERLAP_CONTEXT_SIZE,
    mode="token",
    method="suffix",
    merge=False,
    inplace=False,
)


def chunk(text: str) -> tuple[list[Chunk], list[Chunk]]:
    """Split text into parent chunks with prefix/suffix context and child chunks.

    Args:
        text: Input text to chunk.

    Returns:
        Tuple of (parent_chunks, child_chunks) with relationships established.
    """
    parent_chunks = _parent_chunker.chunk(text)
    prefix_chunks = _prefix_overlapper.refine(parent_chunks)
    suffix_chunks = _suffix_overlapper.refine(parent_chunks)

    parents = []
    children = []
    child_counter = 0

    for parent_idx, parent_chunk in enumerate(parent_chunks):
        parent_id = f"p_{parent_idx}"

        # Create parent with overlapping context
        prefix_ctx = prefix_chunks[parent_idx].context or ""
        suffix_ctx = suffix_chunks[parent_idx].context or ""
        full_text = prefix_ctx + parent_chunk.text + suffix_ctx

        parent_wrapper = Chunk(
            id=parent_id,
            text=full_text,
        )

        # Create children from original parent
        child_chunks = _child_chunker.chunk(parent_chunk.text)
        for child_chunk in child_chunks:
            child_id = f"c_{child_counter}"
            children.append(
                Chunk(
                    id=child_id,
                    text=child_chunk.text,
                    parent_id=parent_id,
                )
            )
            parent_wrapper.child_ids.append(child_id)
            child_counter += 1

        parents.append(parent_wrapper)

    return parents, children
