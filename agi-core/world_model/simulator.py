from __future__ import annotations

from typing import Any

from runtime.models import Observation, PlanRecord


class WorldModel:
    def __init__(self) -> None:
        self.constraints = [
            "actions_must_be_safe",
            "resources_must_be_non_negative",
            "plans_must_have_feasible_sequence",
        ]

    def update_state(self, observation: Observation, *, prior_state: dict[str, Any] | None = None) -> dict[str, Any]:
        state = dict(prior_state or {})
        state["last_observation"] = observation.to_dict()
        state["entities"] = observation.entities
        state["events"] = observation.events
        state["goal_candidates"] = observation.inferred_goals
        state["importance"] = observation.importance
        return state

    def simulate_plan(self, plan: PlanRecord, *, world_state: dict[str, Any]) -> dict[str, Any]:
        risks = [step.risk for step in plan.steps]
        violations = []
        if any("unsafe" in item.lower() for step in plan.steps for item in step.constraints):
            violations.append("unsafe_constraint_detected")
        if not plan.steps:
            violations.append("empty_plan")
        success = max(0.05, min(0.99, plan.predicted_success - (sum(risks) / max(1, len(risks) * 4.0))))
        return {
            "plan_id": plan.plan_id,
            "predicted_success": round(success, 6),
            "constraint_violations": violations,
            "future_state": {
                "active_goal_id": plan.goal_id,
                "step_count": len(plan.steps),
                "world_focus": world_state.get("entities", []),
            },
            "feasible": len(violations) == 0,
        }

    def predict_outcome(self, action_description: str, *, world_state: dict[str, Any]) -> dict[str, Any]:
        lower = action_description.lower()
        outcome = "stable_progress"
        if "delete" in lower or "reset" in lower:
            outcome = "high_risk_side_effect"
        elif "build" in lower or "deploy" in lower:
            outcome = "resource_consumption_with_forward_progress"
        return {
            "action": action_description,
            "outcome": outcome,
            "world_entities": world_state.get("entities", []),
            "confidence": 0.72 if outcome == "stable_progress" else 0.48,
        }
