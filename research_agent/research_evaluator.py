from __future__ import annotations


class ResearchEvaluator:
    def evaluate(self, finding: dict[str, object]) -> dict[str, object]:
        return {"accepted": True, "confidence": 0.74, "finding": finding}
