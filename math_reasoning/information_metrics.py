from __future__ import annotations

import math
from typing import Any


class InformationMetrics:
    def measure(self, *, uncertainty: float, retrieved_memory: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        memory_items = sum(len(items) for items in retrieved_memory.values())
        entropy = -(uncertainty * math.log(max(uncertainty, 1e-6), 2)) if uncertainty > 0 else 0.0
        info_gain = max(0.0, min(1.0, (memory_items * 0.04) + (1.0 - uncertainty) * 0.5))
        return {"entropy": round(entropy, 6), "information_gain": round(info_gain, 6)}
