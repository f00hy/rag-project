"""Central configuration constants for the RAG pipeline."""

# Logging
LOG_LEVEL: str = "INFO"
LOG_FILENAME: str = "app.log"
LOG_FILEMODE: str = "w"

# Chunking
PARENT_CHUNK_SIZE: int = 1024
CHILD_CHUNK_SIZE: int = 256
OVERLAP_CONTEXT_SIZE: float = 0.25

# Embedding
DENSE_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
SPARSE_MODEL_NAME: str = "prithivida/Splade_PP_en_v1"

# Searching
OVERSAMPLING_FACTOR: float = 2.5
TOP_K_CHUNKS: int = 10

# Infrastructure
BUCKET_NAME: str = "rag"
COLLECTION_NAME: str = "child_chunk"
