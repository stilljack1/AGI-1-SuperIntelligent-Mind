from __future__ import annotations

from typing import Any


class CounterfactualEngine:
    def explore(self, likely_future: dict[str, Any]) -> dict[str, Any]:
        return {
            "counterfactual": f"if constraints tighten, {likely_future.get('query', 'the plan')} shifts to a conservative policy",
        }
