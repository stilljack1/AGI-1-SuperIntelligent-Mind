from __future__ import annotations


class UtilityCalculator:
    def expected_utility(self, *, reward: float, success_probability: float, risk: float) -> float:
        return round((reward * success_probability) - risk, 6)
