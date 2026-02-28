from __future__ import annotations

from runtime.models import PlanRecord


class SafetyController:
    def validate_plan(self, plan: PlanRecord) -> dict[str, object]:
        blocked = []
        for step in plan.steps:
            text = step.description.lower()
            if "delete" in text or "wipe" in text or "exfiltrate" in text:
                blocked.append(step.step_id)
            if "unsafe" in " ".join(step.constraints).lower():
                blocked.append(step.step_id)
        return {
            "allowed": len(blocked) == 0,
            "blocked_steps": blocked,
            "reason": "" if not blocked else "harmful_or_unbounded_action_detected",
        }
