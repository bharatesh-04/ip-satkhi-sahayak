from dataclasses import dataclass
from datetime import datetime, timezone
import re
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.db.models import LegalProvision
from app.services.embeddings import embed_hash, cosine


@dataclass
class Retrieved:
    row: LegalProvision
    score: float
    method: str


class HybridRetriever:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _jurisdiction_filter(jurisdictions: list[str]):
        return or_(*[LegalProvision.jurisdiction == j for j in jurisdictions])

    def lexical(self, query: str, jurisdictions: list[str], top_k: int = 20) -> list[Retrieved]:
        """PostgreSQL FTS path; falls back to token overlap for SQLite/dev."""
        try:
            q = func.plainto_tsquery("simple", query)
            stmt = (
                select(LegalProvision, func.ts_rank_cd(func.to_tsvector("simple", LegalProvision.text), q).label("score"))
                .where(self._jurisdiction_filter(jurisdictions))
                .where(LegalProvision.status.in_(["current", "applicable"]))
                .where(func.to_tsvector("simple", LegalProvision.text).op("@@")(q))
                .order_by(func.ts_rank_cd(func.to_tsvector("simple", LegalProvision.text), q).desc())
                .limit(top_k)
            )
            return [Retrieved(row, float(score or 0), "lexical") for row, score in self.db.execute(stmt).all()]
        except Exception:
            rows = self.db.execute(
                select(LegalProvision).where(
                    self._jurisdiction_filter(jurisdictions),
                    LegalProvision.status.in_(["current", "applicable"]),
                ).limit(5000)
            ).scalars().all()
            q_tokens = set(re.findall(r"[\w§.-]+", query.lower()))
            scored = []
            for row in rows:
                r_tokens = set(re.findall(r"[\w§.-]+", row.text.lower()))
                exact = len(q_tokens & r_tokens)
                citation_bonus = 1.0 if any(t in (row.citation or "").lower() for t in q_tokens) else 0.0
                score = exact + citation_bonus
                if score > 0:
                    scored.append(Retrieved(row, float(score), "lexical-fallback"))
            scored.sort(key=lambda x: x.score, reverse=True)
            return scored[:top_k]

    def dense_python(self, query: str, jurisdictions: list[str], top_k: int = 20) -> list[Retrieved]:
        qv = embed_hash(query)
        rows = self.db.execute(
            select(LegalProvision).where(
                self._jurisdiction_filter(jurisdictions),
                LegalProvision.status.in_(["current", "applicable"]),
                LegalProvision.embedding.is_not(None),
            ).limit(5000)
        ).scalars().all()
        ranked = []
        for row in rows:
            try:
                score = cosine(qv, row.embedding)
            except Exception:
                score = 0.0
            ranked.append((score, row))
        ranked.sort(reverse=True, key=lambda x: x[0])
        return [Retrieved(r, float(s), "dense") for s, r in ranked[:top_k]]

    def search(self, query: str, jurisdictions: list[str], top_k: int = 20) -> list[Retrieved]:
        lex = self.lexical(query, jurisdictions, top_k)
        dense = self.dense_python(query, jurisdictions, top_k)
        merged: dict[str, Retrieved] = {}
        for item in lex + dense:
            existing = merged.get(item.row.chunk_id)
            weight = 1.0 if item.method.startswith("lexical") else 0.9
            fused = item.score * weight
            if not existing or fused > existing.score:
                merged[item.row.chunk_id] = Retrieved(item.row, fused, item.method)
        values = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return values[:top_k]
