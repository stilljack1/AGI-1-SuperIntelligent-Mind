from __future__ import annotations

from typing import Any


class TacticalExecutor:
    def select(self, ordered_steps: list[dict[str, Any]]) -> dict[str, Any]:
        if not ordered_steps:
            return {"selected_step_id": "", "mode": "hold"}
        winner = ordered_steps[0]
        return {
            "selected_step_id": winner.get("step_id", ""),
            "mode": "decisive" if float(winner.get("risk", 1.0)) < 0.35 else "cautious",
            "reason": "highest local value under current constraints",
        }
