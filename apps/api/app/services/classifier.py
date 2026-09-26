import re
from app.core.schemas import InnovationProfile, InnovationIngredient

PRODUCT_HINTS = {
    "classical_medicine": ["classical", "first schedule", "authoritative text", "classical formulation"],
    "proprietary_medicine": ["proprietary", "patent and proprietary", "p&p"],
    "new_drug": ["new drug", "clinical trial", "clinical evidence", "safety and effectiveness"],
    "phytopharmaceutical": ["phytopharmaceutical", "standardized extract"],
    "ayurveda_aahar": ["ayurveda aahar", "nutraceutical", "food", "drink", "nutrition", "beverage"],
    "cosmetic": ["cosmetic", "cream", "skin care", "shampoo", "face wash", "serum"],
}

DOMAIN_TERMS = {
    "patents": ["patent", "novel", "inventive step", "prior art", "section 3(p)", "section 3p"],
    "trademarks": ["trademark", "brand", "logo", "mark"],
    "tk": ["traditional knowledge", "tkdl", "traditional use", "classical text", "traditional preparation"],
    "abs": ["biodiversity", "biological resource", "benefit sharing", "abs", "source of origin", "genetic resource"],
    "regulation": ["license", "approval", "drug", "food", "cosmetic", "label", "manufacture", "ayush"],
    "advertising": ["advertising", "claim", "cures", "clinically proven", "treats", "label"],
}

INGREDIENTS = {
    "ashwagandha": "Withania somnifera",
    "turmeric": "Curcuma longa",
    "neem": "Azadirachta indica",
    "tulsi": "Ocimum tenuiflorum",
    "brahmi": "Bacopa monnieri",
    "amla": "Phyllanthus emblica",
}

COUNTRY_PATTERNS = {
    "IN": ["india", "indian", "inr", " in "],
    "DE": ["germany", "german", "eu", "european union"],
    "US": ["usa", "united states", "u.s.", "us market"],
    "AE": ["uae", "united arab emirates", "dubai"],
    "JP": ["japan", "japanese"],
    "AU": ["australia", "australian"],
    "BR": ["brazil", "brazilian"],
}


def _mentions(low: str, options: list[str]) -> bool:
    return any(opt in low for opt in options)


def profile_from_text(text: str) -> InnovationProfile:
    low = text.lower()
    scores = {k: sum(1 for h in hints if h in low) for k, hints in PRODUCT_HINTS.items()}
    best_score = max(scores.values(), default=0)
    category = max(scores, key=scores.get) if best_score else "unknown"

    ingredients = [InnovationIngredient(name=n, scientific_name=sci) for n, sci in INGREDIENTS.items() if n in low]

    intended = [term for term in ["wellness", "stress", "diabetes", "skin care", "nutrition", "immunity", "pain", "sleep"] if term in low]

    claims: list[str] = []
    if any(k in low for k in ["claim", "cures", "treats", "clinically proven"]):
        claims.append(text.strip())

    tk = "yes" if _mentions(low, ["traditional knowledge", "classical text", "traditional preparation", "classical formulation"]) else "unknown"
    bio = "yes" if ingredients else "unknown"
    origin = "IN" if _mentions(low, ["from india", "sourced from india", "indian biological resource"]) else None

    markets: list[str] = []
    padded = f" {low} "
    for code, patterns in COUNTRY_PATTERNS.items():
        if any(p in padded for p in patterns):
            markets.append(code)
    if not markets:
        markets = ["IN"]

    delta = [
        term for term in ["new extraction process", "novel process", "new formulation", "improved delivery", "proprietary composition"]
        if term in low
    ]

    missing: list[str] = []
    if not intended:
        missing.append("intended_use")
    if not claims:
        missing.append("claims")
    if not ingredients:
        missing.append("ingredients")
    if "international" in low and len(markets) == 1:
        missing.append("target_country")

    confidence = 0.55
    if category != "unknown":
        confidence += 0.15
    if ingredients:
        confidence += 0.05
    if intended:
        confidence += 0.05
    if claims:
        confidence += 0.05
    confidence = min(confidence, 0.95)

    return InnovationProfile(
        category=category,
        ingredients=ingredients,
        intended_use=intended,
        claims=claims,
        traditional_knowledge_involvement=tk,
        biological_resource_involvement=bio,
        origin=origin,
        target_markets=markets,
        innovation_delta=delta,
        classification_confidence=confidence,
        missing_facts=missing,
    )


def domains_for(text: str, profile: InnovationProfile) -> list[str]:
    low = text.lower()
    out = [d for d, terms in DOMAIN_TERMS.items() if _mentions(low, terms)]
    if profile.ingredients and "abs" not in out:
        out.append("abs")
    if profile.category != "unknown" and "regulation" not in out:
        out.append("regulation")
    if profile.claims and "advertising" not in out:
        out.append("advertising")
    return sorted(set(out))
