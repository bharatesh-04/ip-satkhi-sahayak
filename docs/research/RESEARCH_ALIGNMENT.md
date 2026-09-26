# Research → Implementation Alignment

| Research basis from supplied project report | Implementation decision |
|---|---|
| Legal RAG Bench (2026) | Treat retrieval as first-class; benchmark retrieval separately. |
| Wu et al., RAG survey | Dense+sparse retrieval, reranking, adaptive retrieval, updates. |
| IEEE legal-RAG survey (2025) | Legal-aware chunking, hybrid retrieval, governance, privacy. |
| LegalGraphRAG (ACL 2026) | Graph retrieval + separated research/audit/synthesis responsibilities. |
| GraphRAG survey | Use graph retrieval for multi-hop relationships, not every lookup. |
| ARES (NAACL 2024) | Evaluate context relevance, faithfulness and answer relevance separately. |
| Self-RAG (ICLR 2024) | Adaptive retrieval/critique for difficult or low-confidence queries. |
| AyuRAG (IEEE CICT 2024) | Domain-specific Ayurveda retrieval. |
| AyurSanvaad (2025) | Multilingual Ayurveda interaction pattern; evaluate legal-meaning preservation. |
| IndicTrans2 (TMLR 2023) | Indian-language translation layer; retain legal terminology carefully. |
| Citation-Closure (2026) | Claim-to-evidence attribution and citation validation. |
| ComplianceNLP (2026) | KG-augmented regulatory gap detection. |
| CSIR-TKDL | Authorized traditional-knowledge prior-art pointer; restricted-access controls. |
| WIPO / IP India / AYUSH / CDSCO / FSSAI / NBA | Operational Tier-1 source registry. |

## Research integrity

Research papers justify architectural and evaluation choices. They are not controlling legal authority. Never claim zero hallucination or 100% legal accuracy.
