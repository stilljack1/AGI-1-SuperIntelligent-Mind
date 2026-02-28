from __future__ import annotations

from typing import Any


class FuturePredictor:
    def predict(self, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(scenarios, key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
        return {"likely_future": ordered[0] if ordered else {}}
