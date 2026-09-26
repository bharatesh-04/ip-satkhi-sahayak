import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.models import SourceDocument, LegalProvision
from app.services.embeddings import embed_hash


def seed():
    init_db()
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    demo = [
        {
            "source_id": "DEMO-IN-IP",
            "title": "Demo: IP India Source Pointer",
            "url": "https://ipindia.gov.in/",
            "authority": "IP India",
            "jurisdiction": "IN",
            "regime": "patents",
            "citation": "IP India — official portal",
            "text": "DEMO EVIDENCE ONLY. Use the current Patents Act, Rules and AYUSH examination guidance from IP India for actual legal assessment. This seed intentionally contains no controlling legal text.",
        },
        {
            "source_id": "DEMO-IN-TK",
            "title": "Demo: CSIR-TKDL Source Pointer",
            "url": "https://www.csir.res.in/en/documents/tkdl",
            "authority": "CSIR-TKDL",
            "jurisdiction": "IN",
            "regime": "traditional_knowledge",
            "citation": "CSIR-TKDL — official information page",
            "text": "DEMO EVIDENCE ONLY. Use authorized TKDL access for traditional-knowledge prior-art screening. Do not expose restricted TKDL content.",
        },
        {
            "source_id": "DEMO-IN-ABS",
            "title": "Demo: National Biodiversity Authority Source Pointer",
            "url": "https://nbaindia.org/",
            "authority": "National Biodiversity Authority",
            "jurisdiction": "IN",
            "regime": "abs",
            "citation": "National Biodiversity Authority — official portal",
            "text": "DEMO EVIDENCE ONLY. Determine current biodiversity and ABS requirements from the National Biodiversity Authority and applicable law/rules/regulations.",
        },
        {
            "source_id": "DEMO-GLOBAL-WIPO",
            "title": "Demo: WIPO Global Framework Pointer",
            "url": "https://www.wipo.int/",
            "authority": "WIPO",
            "jurisdiction": "GLOBAL",
            "regime": "international_ip",
            "citation": "WIPO — official portal",
            "text": "DEMO EVIDENCE ONLY. Apply relevant WIPO treaty/system and destination-country authoritative rules; global frameworks do not replace national market authorization.",
        },
        {
            "source_id": "DEMO-DE-COUNTRY",
            "title": "Demo: Germany Country Profile Pointer",
            "url": "https://www.dpma.de/",
            "authority": "DPMA / EU regulatory sources",
            "jurisdiction": "DE",
            "regime": "country_profile",
            "citation": "Germany/EU — official authority pointer",
            "text": "DEMO EVIDENCE ONLY. Germany/EU requirements must be checked against current official product, IP, import, food, cosmetic and medicinal sources applicable to the product classification.",
        },
    ]
    try:
        for d in demo:
            if db.query(LegalProvision).filter_by(chunk_id=d["source_id"] + ":1").first():
                continue
            if not db.query(SourceDocument).filter_by(source_id=d["source_id"]).first():
                db.add(SourceDocument(
                    source_id=d["source_id"], canonical_url=d["url"], title=d["title"], authority=d["authority"],
                    authority_level="tier_1", jurisdiction=d["jurisdiction"], document_type="demo_seed", access_level="PUBLIC"
                ))
            db.add(LegalProvision(
                chunk_id=d["source_id"] + ":1", source_id=d["source_id"], document_title=d["title"], authority=d["authority"],
                authority_level="tier_1", jurisdiction=d["jurisdiction"], regime=d["regime"], instrument=d["title"],
                page=1, language="en", published_at=now, effective_from=now, version="demo-0.1", status="current",
                citation=d["citation"], access_level="PUBLIC", source_url=d["url"], text=d["text"],
                embedding=embed_hash(d["text"]), demo_only=True
            ))
        db.commit()
        print("Seeded demo evidence")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
