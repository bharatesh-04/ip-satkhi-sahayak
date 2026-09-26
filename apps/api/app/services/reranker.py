import re
from app.services.retrieval import Retrieved

STOP = {"the","a","an","of","to","for","and","or","in","on","is","can","my","this","what","how","do","i"}


def rerank(query: str, candidates: list[Retrieved], top_k: int = 8) -> list[Retrieved]:
    terms = {t.lower() for t in re.findall(r"[A-Za-z0-9_§().-]+", query) if t.lower() not in STOP}
    scored = []
    for c in candidates:
        text = c.row.text.lower()
        exact = sum(1 for t in terms if t in text)
        specificity = 0.15 if c.row.section or c.row.article else 0.0
        authority = {"tier_1": 0.50, "tier_2": 0.20, "tier_3": 0.0}.get(c.row.authority_level, 0.0)
        current = 0.20 if c.row.status in {"current", "applicable"} else 0.0
        score = c.score + 0.08 * exact + specificity + authority + current
        scored.append(Retrieved(c.row, score, "reranked"))
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]
