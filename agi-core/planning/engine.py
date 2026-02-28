from __future__ import annotations

from typing import Any

from runtime.models import GoalRecord, PlanRecord, PlanStep


class PlanningEngine:
    def __init__(self) -> None:
        self._plan_count = 0

    def build_plan(
        self,
        *,
        goal: GoalRecord,
        reasoning: dict[str, Any],
        world_prediction: dict[str, Any],
    ) -> PlanRecord:
        self._plan_count += 1
        base_risk = 1.0 - float(reasoning.get("success_probability", 0.5))
        descriptions = [
            "Clarify target state and constraints",
            "Select lowest-risk action sequence",
            "Execute one bounded action",
            "Verify observed outcome",
            "Store learning and update identity state",
        ]
        steps = []
        for index, description in enumerate(descriptions, start=1):
            action_type = "analyze" if index in {1, 2, 4} else ("respond" if index == 3 else "schedule")
            steps.append(
                PlanStep(
                    step_id=f"plan_{self._plan_count:04d}_step_{index:02d}",
                    description=description,
                    action_type=action_type,
                    expected_outcome=world_prediction.get("outcome", "stable_progress"),
                    risk=round(min(1.0, base_risk + (index * 0.03)), 6),
                    priority=round(max(goal.priority, goal.reward), 6),
                    constraints=["safe", "truthful", "bounded_execution"],
                )
            )
        return PlanRecord(
            plan_id=f"plan_{self._plan_count:04d}",
            goal_id=goal.goal_id,
            strategy="bounded_adaptive_execution",
            confidence=float(reasoning.get("confidence", 0.5)),
            predicted_success=float(reasoning.get("success_probability", 0.5)),
            steps=steps,
        )

    def select_goal(self, goals: list[dict[str, Any]]) -> GoalRecord | None:
        if not goals:
            return None
        item = goals[0]
        return GoalRecord(
            goal_id=str(item["goal_id"]),
            description=str(item["description"]),
            priority=float(item["priority"]),
            urgency=float(item["urgency"]),
            reward=float(item["reward"]),
            source=str(item["source"]),
            status=str(item.get("status", "active")),
            created_at=str(item.get("created_at", "")),
            due_at=item.get("due_at"),
        )
