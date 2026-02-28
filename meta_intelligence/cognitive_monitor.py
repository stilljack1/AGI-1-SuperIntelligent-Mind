from __future__ import annotations

from typing import Any


class CognitiveMonitor:
    def observe(self, *, reasoning: dict[str, Any], alignment: dict[str, Any]) -> dict[str, Any]:
        confidence = float(reasoning.get("confidence", 0.5))
        alignment_score = float(alignment.get("alignment_score", 0.5))
        return {
            "cognitive_load": round(1.0 - confidence + (1.0 - alignment_score) * 0.3, 6),
            "watch_items": [] if confidence >= 0.5 else ["insufficient_confidence"],
        }
