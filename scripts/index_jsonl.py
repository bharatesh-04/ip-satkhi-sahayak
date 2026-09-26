"""Index processed JSONL evidence into the configured SQL store."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.models import SourceDocument, LegalProvision
from app.services.embeddings import embed_hash


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def run(directory: str):
    init_db()
    db = SessionLocal()
    root = Path(directory)
    count = 0
    try:
        for path in sorted(root.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                source_id = item["source_id"]
                source = db.query(SourceDocument).filter_by(source_id=source_id).first()
                if not source:
                    source = SourceDocument(
                        source_id=source_id,
                        canonical_url=item["source_url"],
                        title=item["document_title"],
                        authority=item["authority_name"],
                        authority_level=item.get("authority_level", "tier_1"),
                        jurisdiction=item["jurisdiction"],
                        document_type="ingested",
                        access_level=item.get("access_level", "PUBLIC"),
                        content_hash=item.get("content_hash"),
                    )
                    db.add(source)
                    db.flush()
                existing = db.query(LegalProvision).filter_by(chunk_id=item["chunk_id"]).first()
                if existing:
                    continue
                db.add(LegalProvision(
                    chunk_id=item["chunk_id"], source_id=source_id,
                    document_title=item["document_title"], authority=item["authority_name"],
                    authority_level=item.get("authority_level", "tier_1"),
                    jurisdiction=item["jurisdiction"], regime=item["regime"], instrument=item["document_title"],
                    section=item.get("section"), language=item.get("language", "en"),
                    published_at=parse_dt(item.get("published_at")), effective_from=parse_dt(item.get("effective_from")),
                    effective_to=parse_dt(item.get("effective_to")), version=item.get("version"),
                    status=item.get("status", "current"), citation=item["citation"],
                    access_level=item.get("access_level", "PUBLIC"), source_url=item["source_url"],
                    text=item["text"], embedding=embed_hash(item["text"]), demo_only=bool(item.get("demo_only", False)),
                ))
                count += 1
        db.commit()
        print(f"Indexed {count} evidence units")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--directory", default=str(ROOT / "data" / "processed"))
    args = ap.parse_args()
    run(args.directory)
