from __future__ import annotations

from typing import Any


class GoalManager:
    def build_hierarchy(self, goals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        ordered = sorted(
            goals,
            key=lambda item: (
                float(item.get("priority", 0.0)),
                float(item.get("urgency", 0.0)),
                float(item.get("reward", 0.0)),
            ),
            reverse=True,
        )
        return {
            "root_goals": ordered[:3],
            "supporting_goals": ordered[3:10],
            "deferred_goals": ordered[10:],
        }
