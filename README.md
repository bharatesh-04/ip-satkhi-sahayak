# IP-SAKTI Sahayak — SIH 2026 MVP Codebase

**Problem Statement 26045 • Ministry of Ayush • Team DarkPhoenix**

A source-grounded, jurisdiction-aware AI decision-support prototype for Ayurveda IP, Traditional Knowledge, biodiversity/ABS and product-regulatory navigation.

## Architecture

`Experience → API → Agentic Triage/Profile → Jurisdiction Rule-Wall → Hybrid GraphRAG → Specialist Reasoning → Evidence/Trust → Action`

The implementation follows the supplied SIH PPT architecture and the attached implementation/data/research reports. The core design principle is:

> **The model is downstream of the evidence.**

The repository deliberately separates authoritative legal knowledge from persistent user/innovation memory. Research papers justify techniques; current authoritative legal/regulatory sources determine legal conclusions.

## Implemented prototype capabilities

- Progressive triage + Innovation Profile / Legal Digital Twin
- India vs International routing
- Global Framework + reusable Country Profiles
- Hybrid retrieval: lexical + dense/vector + graph + reranking
- Legal-aware chunking + provenance metadata
- PostgreSQL + pgvector-ready schema
- Neo4j relationship layer
- Redis working-memory integration boundary
- MinIO/S3 evidence-storage integration boundary
- Persistent user/innovation memory
- Optional LangGraph workflow with deterministic fallback
- Specialist role contracts: IP, TK/ABS, Regulatory, International
- Evidence trust gate: authority, jurisdiction, version, citation, conflict
- Safe abstention and human-review signals
- Section 3(p) defensive-screening signal boundary
- Bhashini adapter boundary
- Model/provider abstraction
- Source-update hash monitor
- Evaluation scaffold and gold-set structure
- Next.js / React UI
- Docker Compose for Postgres/pgvector, Neo4j, Redis and MinIO
- CI, tests and architecture/data/research documentation

## Demo-mode boundary

The seeded evidence intentionally contains **source pointers, not controlling legal text**. It is labelled `demo_only=true`. This makes the repository safe to demonstrate the architecture without redistributing restricted TKDL material or pretending that a sample record is current law.

Before operational use, ingest current authorised primary sources, validate them, populate the knowledge graph, select/benchmark real embedding/reranking models and complete the expert-reviewed evaluation set.

## Local development

The code can run without Docker using SQLite for basic endpoint/tests. The intended SIH stack is PostgreSQL + pgvector + Neo4j + Redis + MinIO via Docker Compose.

```bash
cp .env.example .env
python -m compileall -q .
PYTHONPATH=apps/api pytest -q
PYTHONPATH=apps/api python scripts/seed_demo.py
PYTHONPATH=apps/api uvicorn app.main:app --reload --port 8000
```

Web:

```bash
cd apps/web
npm install
npm run dev
```

## Ingestion

```bash
python scripts/ingest_source.py --manifest knowledge/source_manifests/india_core.json
python scripts/index_jsonl.py
```

Restricted/licensed source records are skipped by the generic ingestion path and must use an authorised connector.

## Update monitoring

```bash
python scripts/check_updates.py --manifest knowledge/source_manifests/india_core.json
```

This is a lightweight hash monitor. Production should add authenticated source polling/webhooks, structural legal diffing, curator approval, re-indexing and graph impact analysis as specified in `docs/reference_implementation_spec.md`.

## Evaluation

The supplied research identifies retrieval accuracy, citation correctness, groundedness, classification accuracy, jurisdiction accuracy, multilingual legal fidelity and safe-abstention performance as distinct metrics. See:

- `docs/EVALUATION.md`
- `docs/RESEARCH_ALIGNMENT.md`
- `docs/RESEARCH_TO_CODE.md`
- `evals/gold_set/`

Do not publish target metrics as measured results until the benchmark has actually been executed.

## Source documents included

The attached SIH PPT, Data Architecture Report, Research Report and implementation specification are preserved under `docs/` for traceability.
