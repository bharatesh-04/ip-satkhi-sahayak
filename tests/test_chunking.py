import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
from scripts.ingest_source import legal_chunks


def test_legal_chunking_preserves_section():
    src = {"source_id": "S", "url": "https://x", "authority": "A", "title": "Act", "jurisdiction": "IN", "regime": "patents"}
    chunks = legal_chunks("Preamble\nSection 3(p) Traditional knowledge.\nSection 8 Disclosure.", src)
    assert any(c["section"] == "3(p)" for c in chunks)
    assert any(c["section"] == "8" for c in chunks)
