from __future__ import annotations

from typing import Any


class GoalPriorityEngine:
    def score(self, goal: dict[str, Any]) -> float:
        priority = float(goal.get("priority", 0.0))
        urgency = float(goal.get("urgency", 0.0))
        reward = float(goal.get("reward", 0.0))
        return round((0.45 * priority) + (0.30 * urgency) + (0.25 * reward), 6)

    def rank(self, goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = []
        for goal in goals:
            enriched = dict(goal)
            enriched["priority_score"] = self.score(goal)
            ranked.append(enriched)
        ranked.sort(key=lambda item: float(item["priority_score"]), reverse=True)
        return ranked
