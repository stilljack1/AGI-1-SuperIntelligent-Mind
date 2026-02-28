from __future__ import annotations

from typing import Any


class EthicsReasoner:
    def analyze(self, plan: dict[str, Any]) -> dict[str, Any]:
        harmful = any("delete" in str(step.get("description", "")).lower() for step in plan.get("steps", []))
        return {
            "harm_flag": harmful,
            "primary_principle": "beneficence_and_non_maleficence",
            "ethical_posture": "blocked" if harmful else "permitted",
        }
