from __future__ import annotations

from typing import Any


class StrategySelector:
    def select(self, *, reasoning: dict[str, Any], affect: dict[str, Any]) -> dict[str, Any]:
        uncertainty = float(reasoning.get("uncertainty", 0.5))
        if uncertainty > 0.45:
            mode = "deliberate"
        elif float(affect.get("exploration_drive", 0.0)) > 0.6:
            mode = "exploratory"
        else:
            mode = "efficient"
        return {"strategy_mode": mode, "uncertainty": uncertainty}
