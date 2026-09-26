"""Jurisdiction sandbox ('Rule-Wall') and metadata-driven country profiles."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


class JurisdictionRouter:
    GLOBAL = "GLOBAL"

    def targets(self, mode: str, country: str | None) -> list[str]:
        if mode == "india":
            return ["IN"]
        if not country:
            return [self.GLOBAL]
        return [self.GLOBAL, country.upper()]

    def load_country_profile(self, code: str) -> dict:
        path = ROOT / "knowledge" / "country_profiles" / f"{code.lower()}.json"
        if not path.exists():
            return {
                "country_code": code.upper(),
                "country_name": code.upper(),
                "profile_version": None,
                "status": "not_configured",
            }
        return json.loads(path.read_text(encoding="utf-8"))

    def check(self, evidence_jurisdiction: str, allowed: list[str]) -> bool:
        return evidence_jurisdiction in allowed
