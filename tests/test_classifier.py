import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
from app.services.classifier import profile_from_text, domains_for


def test_classifies_cosmetic():
    p = profile_from_text("I made a turmeric face cream cosmetic for skin care")
    assert p.category == "cosmetic"
    assert "turmeric" in [x.name for x in p.ingredients]


def test_detects_abs_and_patent():
    text = "Can I patent my Ashwagandha formulation using a new extraction process from India?"
    p = profile_from_text(text)
    ds = domains_for(text, p)
    assert "patents" in ds and "abs" in ds
