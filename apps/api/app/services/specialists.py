"""Specialist analysis contracts.

These are intentionally evidence-first rule helpers for the SIH prototype. A production
version can replace each function body with an LLM tool/agent while preserving the
same typed output contract.
"""


def run_specialists(profile, domains: list[str], evidence_ids: list[str], jurisdiction: str) -> dict[str, dict]:
    results: dict[str, dict] = {}
    if "patents" in domains:
        results["ip"] = {
            "role": "IP Agent",
            "finding": "Patent/prior-art screening is relevant; no patentability determination is made here.",
            "evidence_ids": evidence_ids[:2],
        }
    if "tk" in domains:
        results["tk_abs"] = {
            "role": "TK/ABS Agent",
            "finding": "Traditional-knowledge overlap should be screened using authorized evidence.",
            "evidence_ids": evidence_ids[:2],
        }
    if "abs" in domains:
        results["biodiversity"] = {
            "role": "Biodiversity/ABS Agent",
            "finding": "Biological-resource origin and ABS applicability require fact-specific assessment.",
            "evidence_ids": evidence_ids[:2],
        }
    if "regulation" in domains:
        results["regulatory"] = {
            "role": "Regulatory Agent",
            "finding": f"Confirm the product category before relying on a regulatory pathway in {jurisdiction}.",
            "evidence_ids": evidence_ids[:2],
        }
    if jurisdiction != "IN":
        results["international"] = {
            "role": "International Agent",
            "finding": "Apply the selected country profile together with global frameworks; do not import unrelated national rules.",
            "evidence_ids": evidence_ids[:2],
        }
    return results
