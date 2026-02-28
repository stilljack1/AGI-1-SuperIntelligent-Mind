from __future__ import annotations


class RiskModel:
    def score(self, *, uncertainty: float, alignment_penalty: float) -> float:
        return round(max(0.0, min(1.0, (0.65 * uncertainty) + (0.35 * alignment_penalty))), 6)
