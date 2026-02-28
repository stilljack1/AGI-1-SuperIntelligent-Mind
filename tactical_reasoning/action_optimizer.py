from __future__ import annotations

from typing import Any


class ActionOptimizer:
    def reorder(self, steps: list[dict[str, Any]], *, urgency: float) -> list[dict[str, Any]]:
        ranked = []
        for step in steps:
            score = float(step.get("priority", 0.0)) - float(step.get("risk", 0.0)) + (0.2 * urgency)
            enriched = dict(step)
            enriched["tactical_score"] = round(score, 6)
            ranked.append(enriched)
        ranked.sort(key=lambda item: float(item["tactical_score"]), reverse=True)
        return ranked
