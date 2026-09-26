import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
from app.core.schemas import Evidence, Claim, ConsultationRequest, JurisdictionMode
from app.services.trust import EvidenceTrust


def ev(j="IN", status="current", access="PUBLIC", demo=False):
    return Evidence(evidence_id="E1", source_id="S1", source_url="https://example.org", authority_level="tier_1", authority_name="Official", document_title="Demo", jurisdiction=j, regime="ip", citation="Demo, s.1", text="demo", status=status, access_level=access, demo_only=demo)


def test_trust_accepts_current_in_demo():
    r = EvidenceTrust({"PUBLIC"}, demo_mode=True).verify([ev(demo=True)], ["IN"], [Claim(claim_id="c1", text="x")])
    assert r.eligible and r.confidence > 0


def test_trust_blocks_wrong_jurisdiction():
    r = EvidenceTrust({"PUBLIC"}, demo_mode=True).verify([ev("DE", demo=True)], ["IN"], [Claim(claim_id="c1", text="x")])
    assert not r.eligible and r.needs_human


def test_international_consult_requires_target_country():
    with pytest.raises(ValidationError):
        ConsultationRequest(
            message="Need advice for export into Europe",
            jurisdiction_mode=JurisdictionMode.international,
            target_country=None,
        )


def test_country_code_is_normalized_and_validated():
    req = ConsultationRequest(
        message="Need advice for export into Germany",
        jurisdiction_mode=JurisdictionMode.international,
        target_country="de",
    )
    assert req.target_country == "DE"

    with pytest.raises(ValidationError):
        ConsultationRequest(
            message="Need advice for export into unknown market",
            jurisdiction_mode=JurisdictionMode.international,
            target_country="ZZ",
        )
