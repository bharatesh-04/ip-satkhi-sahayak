"""CLI demo for the IP-SAKTI evidence-first workflow."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.core.schemas import ConsultationRequest, JurisdictionMode
from app.services.orchestrator import Orchestrator


async def main(message: str, mode: str, country: str | None):
    init_db()
    db = SessionLocal()
    try:
        result = await Orchestrator(db).run(ConsultationRequest(
            message=message,
            language="en",
            jurisdiction_mode=JurisdictionMode(mode),
            target_country=country,
            user_id="demo-user",
        ))
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="I have developed a turmeric-based Ayurvedic formulation and want to sell it in Germany. Can I protect it and what should I check?")
    parser.add_argument("--mode", choices=["india", "international"], default="international")
    parser.add_argument("--country", default="DE")
    args = parser.parse_args()
    asyncio.run(main(args.message, args.mode, args.country if args.mode == "international" else None))
