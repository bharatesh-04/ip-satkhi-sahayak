from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.schemas import Evidence, Claim


@dataclass
class TrustResult:
    eligible: list[Evidence]
    warnings: list[str]
    confidence: float
    needs_human: bool


class EvidenceTrust:
    def __init__(self, allowed_access: set[str] | None = None, demo_mode: bool = False):
        self.allowed_access = allowed_access or {"PUBLIC"}
        self.demo_mode = demo_mode

    def verify(self, evidence: list[Evidence], jurisdictions: list[str], claims: list[Claim]) -> TrustResult:
        warnings: list[str] = []
        eligible: list[Evidence] = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        for e in evidence:
            if e.access_level not in self.allowed_access:
                warnings.append(f"Restricted evidence blocked: {e.evidence_id}")
                continue
            if e.jurisdiction not in jurisdictions and e.jurisdiction != "GLOBAL":
                warnings.append(f"Jurisdiction mismatch: {e.evidence_id}")
                continue
            if e.status not in {"current", "applicable"}:
                warnings.append(f"Outdated evidence: {e.evidence_id}")
                continue
            if e.effective_from and e.effective_from > now:
                warnings.append(f"Not yet effective: {e.evidence_id}")
                continue
            if e.effective_to and e.effective_to < now:
                warnings.append(f"Expired evidence: {e.evidence_id}")
                continue
            if not e.source_url or not e.citation:
                warnings.append(f"Citation unresolved: {e.evidence_id}")
                continue
            if e.demo_only and not self.demo_mode:
                warnings.append(f"Demo evidence blocked in production: {e.evidence_id}")
                continue
            e.verified = True
            eligible.append(e)

        if not eligible:
            return TrustResult([], warnings + ["No evidence cleared the trust gate."], 0.0, True)

        primary = sum(1 for e in eligible if e.authority_level == "tier_1") / len(eligible)
        freshness = sum(1 for e in eligible if e.status == "current") / len(eligible)
        confidence = min(0.98, 0.35 + 0.35 * primary + 0.20 * freshness + 0.02 * min(len(eligible), 5))
        needs_human = confidence < 0.72 or any("mismatch" in w.lower() or "outdated" in w.lower() or "conflict" in w.lower() for w in warnings)
        return TrustResult(eligible, warnings, round(confidence, 3), needs_human)
