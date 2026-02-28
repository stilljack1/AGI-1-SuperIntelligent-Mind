from __future__ import annotations

import hashlib
import math
from typing import Iterable


def deterministic_hash_embedding(text: str, dims: int = 48) -> list[float]:
    """
    Lightweight deterministic fallback embedding.

    This is intentionally simple so local mode does not depend on cloud embedding APIs.
    """
    payload = text.encode("utf-8", errors="ignore")
    digest = hashlib.sha256(payload).digest()
    vector: list[float] = []
    seed = digest
    while len(vector) < dims:
        seed = hashlib.sha256(seed).digest()
        for idx in range(0, len(seed), 2):
            if len(vector) >= dims:
                break
            chunk = int.from_bytes(seed[idx : idx + 2], byteorder="big", signed=False)
            value = (chunk / 65535.0) * 2.0 - 1.0
            vector.append(value)
    return normalize(vector)


def dot(a: Iterable[float], b: Iterable[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def magnitude(vec: Iterable[float]) -> float:
    return math.sqrt(float(sum(x * x for x in vec)))


def normalize(vec: list[float]) -> list[float]:
    mag = magnitude(vec)
    if mag <= 1e-12:
        return [0.0 for _ in vec]
    return [x / mag for x in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    min_len = min(len(a), len(b))
    return dot(a[:min_len], b[:min_len])
