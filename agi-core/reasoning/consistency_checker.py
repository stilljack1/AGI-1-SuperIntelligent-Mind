from __future__ import annotations

from typing import Any


class ConsistencyChecker:
    def check(self, *, world_state: dict[str, Any], retrieved_memory: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        contradictions = []
        events = {str(event).lower() for event in world_state.get("events", [])}
        episodic = " ".join(str(item).lower() for item in retrieved_memory.get("episodic", []))
        if "success" in episodic and "failure" in episodic and "executed_action" in episodic:
            contradictions.append("mixed_outcome_history")
        if "delete" in events and "preserve" in events:
            contradictions.append("world_state_goal_conflict")
        return {"contradictions": contradictions, "consistent": len(contradictions) == 0}
