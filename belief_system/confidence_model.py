from __future__ import annotations


class ConfidenceModel:
    def score(self, *, evidence_count: int, uncertainty: float) -> float:
        return round(max(0.0, min(1.0, (0.08 * evidence_count) + (1.0 - uncertainty) * 0.45)), 6)
