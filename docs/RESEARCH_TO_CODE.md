# Research-to-Code Notes

The supplied Research Report identifies the strongest methods as:

- LegalGraphRAG / graph-assisted legal reasoning → `Neo4j + specialist orchestration`.
- Legal RAG Bench → `retrieval-first evaluation`.
- LegalBench-RAG → `precise passage retrieval + citation grounding`.
- ARES → `context relevance + faithfulness + answer relevance` evaluation.
- Self-RAG → `adaptive retrieval/critique for difficult queries`.
- AyuRAG / AyurSanvaad → `Ayurveda-domain retrieval + multilingual flow`.
- IndicTrans2 → `Indian-language translation layer`.
- Citation-Closure → `claim-to-evidence mapping`.
- ComplianceNLP → `KG-augmented regulatory gap detection`.

The implementation therefore treats retrieval, provenance, versioning, verification and evaluation as first-class engineering concerns rather than relying on a large model alone.
