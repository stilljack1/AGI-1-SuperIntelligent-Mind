from __future__ import annotations

from typing import Any


class OptimizationEngine:
    def objective(self, *, reward: float, uncertainty_reduction: float, curiosity: float, alignment: float, stability: float) -> dict[str, Any]:
        value = (0.30 * reward) + (0.20 * uncertainty_reduction) + (0.15 * curiosity) + (0.20 * alignment) + (0.15 * stability)
        return {
            "J_total": round(value, 6),
            "weights": {"alpha": 0.30, "beta": 0.20, "gamma": 0.15, "delta": 0.20, "epsilon": 0.15},
        }

    def gradient_step(self, *, current: float, target: float, learning_rate: float = 0.1) -> float:
        return round(current + (learning_rate * (target - current)), 6)
