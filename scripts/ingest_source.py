"""Controlled source ingestion for IP-SAKTI.

Supports HTML/PDF/local files and preserves original artifacts. This script intentionally
skips RESTRICTED/LICENSED sources unless an authorized connector is implemented.
"""
import argparse
import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import httpx

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

ROOT = Path(__file__).resolve().parents[1]


def extract_pdf(path: Path) -> str:
    if fitz is None:
        raise RuntimeError("PyMuPDF is not installed; install requirements or supply HTML/text.")
    doc = fitz.open(path)
    return "\n".join(page.get_text("text") for page in doc)


def extract_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path)
    return path.read_text(encoding="utf-8", errors="replace")


def legal_chunks(text: str, source: dict) -> list[dict]:
    # Split at legal anchors while retaining the matched marker inside the chunk.
    parts = re.split(r"(?=\b(?:Section|Article|Rule|Clause|Schedule)\s+[0-9A-Za-z().-]+)", text)
    chunks = []
    for idx, raw in enumerate((p.strip() for p in parts if p.strip()), 1):
        first = re.search(r"\b(Section|Article|Rule|Clause|Schedule)\s+([0-9A-Za-z().-]+)", raw)
        marker_type = first.group(1) if first else None
        marker_value = first.group(2) if first else None
        section = marker_value if marker_type == "Section" else None
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        chunks.append({
            "chunk_id": f"{source['source_id']}:{idx}",
            "source_id": source["source_id"],
            "source_url": source["url"],
            "authority_level": source.get("tier", "tier_1"),
            "authority_name": source["authority"],
            "document_title": source["title"],
            "jurisdiction": source["jurisdiction"],
            "regime": source["regime"],
            "citation": f"{source['title']}{', s.' + section if section else ''}",
            "section": section,
            "language": source.get("language", "en"),
            "status": "current",
            "access_level": source.get("access_level", "PUBLIC"),
            "version": source.get("version", datetime.now(timezone.utc).date().isoformat()),
            "text": raw,
            "content_hash": digest,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        })
    return chunks


async def fetch(url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": "IP-SAKTI-source-ingestor/0.1"}) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "html" in content_type and BeautifulSoup:
            return BeautifulSoup(response.text, "html.parser").get_text("\n")
        return response.text


async def main(manifest_path: str):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    raw_root = ROOT / "data" / "raw"
    processed_root = ROOT / "data" / "processed"
    raw_root.mkdir(parents=True, exist_ok=True)
    processed_root.mkdir(parents=True, exist_ok=True)

    for source in manifest["sources"]:
        if source.get("access_level") in {"RESTRICTED", "LICENSED", "AUTHENTICATED"}:
            print(f"SKIP restricted/licensed source: {source['source_id']}")
            continue
        try:
            if source.get("local_path"):
                text = extract_file(ROOT / source["local_path"])
            else:
                text = await fetch(source["url"])
            (raw_root / f"{source['source_id']}.txt").write_text(text, encoding="utf-8")
            chunks = legal_chunks(text, source)
            with (processed_root / f"{source['source_id']}.jsonl").open("w", encoding="utf-8") as handle:
                for chunk in chunks:
                    handle.write(json.dumps(chunk, ensure_ascii=True) + "\n")
            print(f"INGESTED {source['source_id']}: {len(chunks)} chunks")
        except Exception as exc:
            print(f"ERROR {source['source_id']}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.manifest))
