# IP-SAKTI Sahayak — Codebase Manifest

## Basis used

This codebase was assembled from the uploaded:

- SIH 2026 DarkPhoenix PPT / Technical Approach
- Production Implementation Specification (`implementation.md`)
- IP-SAKTI Sahayak Research Report
- IP-SAKTI Sahayak Data & Database Architecture Report

The repository preserves those source documents under `docs/` for traceability.

## MVP implementation status

### Working in the available local environment
- Python backend imports
- FastAPI health/root/country endpoints
- SQLite development fallback
- Database model creation without pgvector package
- Deterministic feature-hash embedding baseline
- Legal-aware chunking
- Classification heuristics
- Hybrid lexical+dense retrieval fallback
- Reranking baseline
- Jurisdiction isolation
- Persistent profile/memory CRUD
- Evidence trust gate
- Demo seed data
- CLI demo
- Tests

### Requires dependency/infrastructure setup
- PostgreSQL + pgvector
- Neo4j
- Redis
- MinIO/S3
- LangGraph package for live graph execution
- Real multilingual embedding model
- Cross-encoder reranker
- Live LLM provider
- Bhashini credentials
- Production source ingestion and curator validation

### Intentionally not bundled
- Restricted TKDL content
- Unlicensed paid databases
- Unverified bulk legal corpus
- Claims of production legal accuracy

## Validation performed

- Python compileall: PASS
- pytest: PASS (7 tests)
- FastAPI endpoint smoke tests: PASS
- Demo database seed: PASS

The local environment did not provide Docker/Neo4j/pgvector/LangGraph/frontend npm dependencies, so infrastructure-dependent components are provided as production adapters and Docker configuration rather than falsely claiming they were exercised here.
