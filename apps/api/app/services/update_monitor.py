"""Source change monitor.

This is a lightweight hash/diff monitor for Tier-1/Tier-2 sources. Production deployments
can schedule it with a worker/cron and route approved changes into the ingestion pipeline.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
import httpx

ROOT = Path(__file__).resolve().parents[4]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def check_manifest(manifest_path: str) -> list[dict]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    results = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": "IP-SAKTI-update-monitor/0.1"}) as client:
        for source in manifest.get("sources", []):
            if source.get("access_level") in {"RESTRICTED", "LICENSED", "AUTHENTICATED"}:
                results.append({"source_id": source["source_id"], "status": "restricted_skip"})
                continue
            try:
                response = await client.get(source["url"])
                response.raise_for_status()
                digest = sha256_text(response.text)
                raw_path = ROOT / "data" / "raw" / f"{source['source_id']}.sha256"
                previous = raw_path.read_text(encoding="utf-8").strip() if raw_path.exists() else None
                status = "unchanged" if previous == digest else "changed" if previous else "new"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(digest, encoding="utf-8")
                results.append({"source_id": source["source_id"], "host": urlparse(source["url"]).netloc, "status": status, "sha256": digest})
            except Exception as exc:
                results.append({"source_id": source["source_id"], "status": "error", "error": type(exc).__name__})
    return results
