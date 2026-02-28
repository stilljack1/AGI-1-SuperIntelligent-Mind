from __future__ import annotations

from typing import Any


class InferenceEngine:
    def infer(self, *, query: str, world_state: dict[str, Any], retrieved_memory: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        inferences = [
            {"type": "goal", "value": query},
            {"type": "world_focus", "value": world_state.get("goal_candidates", [])},
            {"type": "memory_support", "value": sum(len(items) for items in retrieved_memory.values())},
        ]
        return {"inferences": inferences}
