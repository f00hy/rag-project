"""Chunking service for parent-child hierarchical text chunking."""

from chonkie import RecursiveChunker, OverlapRefinery
from tokenizers import Tokenizer
from pydantic import BaseModel

tokenizer = Tokenizer.from_pretrained("prithivida/Splade_PP_en_v1")

parent_chunker = RecursiveChunker.from_recipe(
    name="markdown",
    lang="en",
    tokenizer=tokenizer,
    chunk_size=1024,
    min_characters_per_chunk=12,
)

child_chunker = RecursiveChunker.from_recipe(
    name="markdown",
    lang="en",
    tokenizer=tokenizer,
    chunk_size=256,
    min_characters_per_chunk=12,
)

prefix_overlapper = OverlapRefinery(
    tokenizer=tokenizer,
    context_size=0.25,
    mode="token",
    method="prefix",
    merge=False,
    inplace=False,
)

suffix_overlapper = OverlapRefinery(
    tokenizer=tokenizer,
    context_size=0.25,
    mode="token",
    method="suffix",
    merge=False,
    inplace=False,
)


class RelationalChunk(BaseModel):
    """Wrapper for chunk with parent-child relationships."""

    text: str
    chunk_id: str
    parent_id: str | None = None
    child_ids: list[str] = []


def chunk(text: str) -> tuple[list[RelationalChunk], list[RelationalChunk]]:
    """Chunk text into parent-child hierarchy.

    Args:
        text: Text to chunk

    Returns:
        Tuple of (parent_chunks, child_chunks)
    """
    parent_chunks = parent_chunker.chunk(text)
    prefix_chunks = prefix_overlapper.refine(parent_chunks)
    suffix_chunks = suffix_overlapper.refine(parent_chunks)

    parents = []
    children = []
    child_counter = 0

    for parent_idx, parent_chunk in enumerate(parent_chunks):
        parent_id = f"p_{parent_idx}"

        # Add overlap context
        prefix_ctx = prefix_chunks[parent_idx].context or ""
        suffix_ctx = suffix_chunks[parent_idx].context or ""
        full_text = prefix_ctx + parent_chunk.text + suffix_ctx

        parent_wrapper = RelationalChunk(
            text=full_text,
            chunk_id=parent_id,
        )

        # Create children from original parent text (without overlap)
        child_chunks = child_chunker.chunk(parent_chunk.text)
        for child_chunk in child_chunks:
            child_id = f"c_{child_counter}"
            children.append(
                RelationalChunk(
                    text=child_chunk.text,
                    chunk_id=child_id,
                    parent_id=parent_id,
                )
            )
            parent_wrapper.child_ids.append(child_id)
            child_counter += 1

        parents.append(parent_wrapper)

    return parents, children
