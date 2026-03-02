# RAG Project

### TODO
- [ ] Query processing
- [ ] Answer generation
- [ ] API endpoints
- [ ] Testing & Performance Evaluation

### Current Tech Stack
##### Services
- Crawl4AI for web crawling
- Chonkie for chunking
- FastEmbed for embedding
- SQLModel for ORM

##### Infrastructure
- Cloudflare R2 for object store
- Qdrant for vector database
- Supabase for relational database

##### Tools
- uv for package management
- ruff for formatting and linting
- ty for type checking
- pre-commit for Git hooks management
- GitHub Actions, Docker, Docker Compose for CI/CD
- Git for version control

### Current Features
- BFS web crawling
- Parent-child ingestion/retrieval
- Content-hash checking
- Stale-data cleaning
- Hybrid retrieval with RRF
- Reranking with Cross Encoder
