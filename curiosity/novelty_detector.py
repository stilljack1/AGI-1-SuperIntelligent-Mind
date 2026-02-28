from __future__ import annotations

from typing import Any


class NoveltyDetector:
    def detect(self, *, query: str, retrieved_memory: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
        memory_hits = sum(len(items) for items in retrieved_memory.values())
        novelty = max(0.0, min(1.0, 0.9 - (memory_hits * 0.03)))
        return {"novelty_score": round(novelty, 6), "memory_hits": float(memory_hits)}
