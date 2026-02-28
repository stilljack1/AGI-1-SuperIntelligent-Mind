from __future__ import annotations

from typing import Any


class SituationalAnalysis:
    def analyze(self, *, world_state: dict[str, Any], reasoning: dict[str, Any]) -> dict[str, Any]:
        urgency = 0.8 if world_state.get("goal_candidates") else 0.45
        return {
            "urgency": urgency,
            "confidence": float(reasoning.get("confidence", 0.5)),
            "risk_window": round(1.0 - float(reasoning.get("success_probability", 0.5)), 6),
        }
