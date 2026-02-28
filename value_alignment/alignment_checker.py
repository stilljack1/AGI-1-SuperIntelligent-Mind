from __future__ import annotations

from typing import Any


class AlignmentChecker:
    def check(self, *, moral_result: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        blocked = bool(moral_result.get("alignment_score", 0.0) < 0.35)
        return {
            "allowed": not blocked,
            "alignment_score": float(moral_result.get("alignment_score", 0.0)),
            "reason": "" if not blocked else "alignment_score_below_threshold",
            "steps_evaluated": len(plan.get("steps", [])),
        }
