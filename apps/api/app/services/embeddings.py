"""Embedding adapters.

The offline baseline uses a deterministic feature-hash embedding so tests/demo work
without downloading a model. Production should benchmark EmbeddingGemma or another
multilingual legal embedding model and switch the provider through configuration.
"""
import hashlib
import math
import re
from typing import Sequence

DIM = 384


def embed_hash(text: str) -> list[float]:
    """Stable lightweight bag-of-words + character-ngram feature hashing."""
    vec = [0.0] * DIM
    tokens = re.findall(r"[\w§.-]+", text.lower(), flags=re.UNICODE)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % DIM
        sign = 1.0 if digest[4] & 1 else -1.0
        vec[idx] += sign
        # character features help tolerate spelling/inflection variants
        for n in (3, 4):
            for i in range(max(0, len(token) - n + 1)):
                ng = token[i:i+n]
                d = hashlib.md5(ng.encode("utf-8"), usedforsecurity=False).digest()
                j = int.from_bytes(d[:4], "big") % DIM
                vec[j] += 0.15 * (1.0 if d[4] & 1 else -1.0)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
