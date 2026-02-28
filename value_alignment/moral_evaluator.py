from __future__ import annotations

from typing import Any


class MoralEvaluator:
    def evaluate(self, ethics: dict[str, Any]) -> dict[str, Any]:
        alignment_score = ethics["human_utility"] - ethics["harm_penalty"] + ethics["fairness_score"]
        return {
            "alignment_score": round(max(0.0, min(1.0, alignment_score / 2.0)), 6),
            "verdict": "pass" if alignment_score >= 0.8 else "review",
        }
