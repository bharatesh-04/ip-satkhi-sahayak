# IP-SAKTI Sahayak — Research → PPT → Implementation Map

This file is the bridge between the submitted SIH architecture, the Data & Database Architecture report, the Research Report, and the code repository.

| Evidence / design | Repository implementation |
|---|---|
| Dynamic Legal Reasoning Loop | `apps/api/app/services/orchestrator.py` + optional `workflow.py` |
| Agentic orchestration | `workflow.py`, `specialists.py`, LangGraph adapter |
| Innovation Profile / Legal Digital Twin | `classifier.py`, `MemoryManager`, `InnovationProfile` schema |
| Rule-Wall / jurisdiction isolation | `jurisdiction.py`, retrieval jurisdiction filters, country profiles |
| Hybrid GraphRAG | `retrieval.py`, `reranker.py`, `graph.py`, `knowledge/ontologies/` |
| Version-aware evidence | `LegalVersion`, evidence metadata, `update_monitor.py` |
| Source hierarchy | `knowledge/source_manifests/` and `docs/DATA_GOVERNANCE.md` |
| Legal-aware chunking | `scripts/ingest_source.py` |
| Polyglot storage | PostgreSQL + pgvector + Neo4j + Redis + MinIO/S3 in `docker-compose.yml` |
| Persistent memory | `memory.py`, `MemoryRow`, `InnovationProfileRow` |
| Evidence trust gate | `trust.py` |
| Claim-to-evidence contract | `Evidence`, `Claim`, orchestrator evidence package |
| Safe abstention | `trust.py` + orchestrator finalization |
| Multilingual path | `bhashini.py`, multilingual configuration and terminology policy |
| LLM abstraction | `llm.py` + `model_router.py` |
| Human escalation | response contract + UI hook + future escalation service boundary |
| Evaluation | `evals/gold_set/`, `scripts/run_eval.py`, `docs/EVALUATION.md` |

## Source-of-truth rule

Research papers justify architecture and evaluation. Current Tier-1 legal/regulatory sources determine legal conclusions. The implementation deliberately avoids copying restricted TKDL content into the public repository.
