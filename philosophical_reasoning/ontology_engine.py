from __future__ import annotations

from typing import Any


class OntologyEngine:
    def classify(self, world_state: dict[str, Any]) -> dict[str, list[str]]:
        entities = world_state.get("entities", [])
        return {
            "agents": [entity for entity in entities if str(entity).istitle()],
            "processes": [event for event in world_state.get("events", [])],
            "goals": [goal for goal in world_state.get("goal_candidates", [])],
        }
