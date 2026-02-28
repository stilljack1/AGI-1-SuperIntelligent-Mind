from __future__ import annotations

from typing import Any


class StateSpaceModel:
    def encode(self, world_state: dict[str, Any]) -> dict[str, Any]:
        vector = [
            float(len(world_state.get("entities", []))),
            float(len(world_state.get("events", []))),
            float(len(world_state.get("goal_candidates", []))),
            float(world_state.get("importance", 0.0)),
        ]
        return {"state_vector": vector, "dimension": len(vector)}
