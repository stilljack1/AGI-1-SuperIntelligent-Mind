from __future__ import annotations

from typing import Any

from decision_engine.risk_model import RiskModel
from decision_engine.utility_calculator import UtilityCalculator


class DecisionEvaluator:
    def __init__(self) -> None:
        self.risk_model = RiskModel()
        self.utility = UtilityCalculator()

    def evaluate(self, *, options: list[dict[str, Any]], uncertainty: float, alignment_penalty: float) -> dict[str, Any]:
        scored = []
        for option in options:
            risk = self.risk_model.score(uncertainty=uncertainty + float(option.get("risk", 0.0)) * 0.25, alignment_penalty=alignment_penalty)
            utility = self.utility.expected_utility(
                reward=float(option.get("reward", 0.5)),
                success_probability=float(option.get("success_probability", 0.5)),
                risk=risk,
            )
            enriched = dict(option)
            enriched["decision_risk"] = risk
            enriched["expected_utility"] = utility
            scored.append(enriched)
        scored.sort(key=lambda item: float(item["expected_utility"]), reverse=True)
        return {"best": scored[0] if scored else {}, "ranked": scored}
