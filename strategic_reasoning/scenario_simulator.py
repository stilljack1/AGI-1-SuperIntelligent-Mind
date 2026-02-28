from __future__ import annotations

from typing import Any


class ScenarioSimulator:
    def simulate(self, *, goal: str, world_state: dict[str, Any]) -> list[dict[str, Any]]:
        importance = float(world_state.get("importance", 0.5))
        return [
            {"name": "conservative", "reward": round(0.55 + (importance * 0.15), 6), "risk": 0.18, "horizon": 3},
            {"name": "balanced", "reward": round(0.65 + (importance * 0.18), 6), "risk": 0.24, "horizon": 6},
            {"name": "exploratory", "reward": round(0.72 + (importance * 0.20), 6), "risk": 0.34, "horizon": 9},
        ]
