# Prototype build status

## Included now

- Backend FastAPI scaffold and working controlled query pipeline
- PostgreSQL/pgvector schema
- Persistent memory models + manager
- Hybrid retrieval interfaces + reranking
- Legal-aware ingestion/chunking script
- Neo4j graph adapter and ontology
- Evidence trust gate + jurisdiction/version/access checks
- Safe abstention
- Country profile packages
- Next.js UI
- Demo seed + evaluation scaffold
- Research alignment and source register
- Docker Compose for PostgreSQL/pgvector, Neo4j, Redis and MinIO

## Explicitly left as adapters/placeholders

- Live Bhashini credentials/provider integration
- Production LLM credentials/model serving
- Full source-by-source legal corpus ingestion
- Restricted TKDL access (must be licensed/authorized)
- Production cross-encoder reranker selection after benchmark
- Kubernetes deployment hardening
- Expert-reviewed legal gold set

These are intentionally separated so no unsupported or unauthorized legal dataset is silently embedded in the repository.
