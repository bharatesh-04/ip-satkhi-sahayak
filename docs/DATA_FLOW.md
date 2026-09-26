# Data Flow — IP-SAKTI Sahayak

## Ingestion

`Discover → Fetch → Hash/Dedupe → Provenance → Extract → Normalize → Legal Structure → Chunk → Metadata → Entity/Relationship Extraction → Index → Validate → Publish → Monitor`

## Query

`User → NLP/Intent → Innovation Profile → Jurisdiction/Domain Plan → BM25 + Vector + Graph → Merge/Rerank → Evidence Gate → Specialist Reasoning → Citation/Version/Conflict Checks → Actionable Response`

## Storage responsibilities

- **PostgreSQL:** system-of-record, legal metadata, users, consultations, innovation profiles and audit events.
- **pgvector:** semantic embeddings for legal evidence.
- **Neo4j:** cross-domain relationships among products, ingredients, TK, ABS, IP, regulations and jurisdictions.
- **MinIO/S3:** original evidence snapshots, OCR outputs and manifests.
- **Redis:** short-lived session/agent state and safe cache.

## Memory boundary

Persistent user/innovation memory is contextual and must never be treated as legal authority. Current authoritative evidence is retrieved and verified for every material legal recommendation.
