import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
from app.services.embeddings import embed_hash, cosine


def test_hash_embedding_is_stable():
    a = embed_hash("Section 3(p) traditional knowledge")
    b = embed_hash("Section 3(p) traditional knowledge")
    assert len(a) == 384
    assert cosine(a, b) > 0.99
