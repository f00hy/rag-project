# Chunking
PARENT_CHUNK_SIZE: int = 1024
CHILD_CHUNK_SIZE: int = 256
OVERLAP_CONTEXT_SIZE: float = 0.25

# Embedding
DENSE_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
SPARSE_MODEL_NAME: str = "prithivida/Splade_PP_en_v1"

# Infrastructure
BUCKET_NAME: str = "rag"
COLLECTION_NAME: str = "child_chunk"
