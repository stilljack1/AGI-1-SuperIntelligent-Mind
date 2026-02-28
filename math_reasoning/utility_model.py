from __future__ import annotations

from typing import Any


class UtilityModel:
    def evaluate(self, options: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = []
        for option in options:
            utility = (
                (0.5 * float(option.get("reward", 0.0)))
                + (0.3 * float(option.get("success_probability", 0.0)))
                - (0.2 * float(option.get("risk", 0.0)))
            )
            enriched = dict(option)
            enriched["utility"] = round(utility, 6)
            ranked.append(enriched)
        ranked.sort(key=lambda item: float(item["utility"]), reverse=True)
        return {"best": ranked[0] if ranked else {}, "ranked": ranked}
