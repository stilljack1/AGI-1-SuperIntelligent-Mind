from __future__ import annotations

from typing import Any


class EthicsReasoner:
    def score(self, *, plan: dict[str, Any], world_state: dict[str, Any]) -> dict[str, Any]:
        harmful = any("delete" in str(step.get("description", "")).lower() for step in plan.get("steps", []))
        fairness = 0.85 if world_state.get("entities") else 0.7
        human_utility = 0.82 if not harmful else 0.25
        harm_penalty = 0.0 if not harmful else 0.9
        return {
            "human_utility": round(human_utility, 6),
            "harm_penalty": round(harm_penalty, 6),
            "fairness_score": round(fairness, 6),
        }
