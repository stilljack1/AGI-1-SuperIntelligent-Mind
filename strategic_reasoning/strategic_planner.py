from __future__ import annotations

from typing import Any


class StrategicPlanner:
    def plan(
        self,
        *,
        goal_hierarchy: dict[str, list[dict[str, Any]]],
        long_term_strategy: dict[str, Any],
        world_state: dict[str, Any],
    ) -> dict[str, Any]:
        roots = goal_hierarchy.get("root_goals", [])
        objective = roots[0]["description"] if roots else "maintain_coherent_progress"
        return {
            "strategic_objective": objective,
            "time_horizon": long_term_strategy.get("best", {}).get("horizon", 3),
            "resource_posture": "balanced" if float(world_state.get("importance", 0.5)) < 0.75 else "focused",
            "selected_strategy": long_term_strategy.get("best", {}),
        }
