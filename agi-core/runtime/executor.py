from __future__ import annotations

import time
from typing import Any

from runtime.models import ExecutionResult, PlanStep


class ActionExecutor:
    """Safe local executor that simulates or records plan execution."""

    def execute(self, step: PlanStep, *, world_state: dict[str, Any]) -> ExecutionResult:
        started = time.perf_counter()
        if step.action_type == "respond":
            details = f"Generated response for: {step.description}"
            changes = {"last_response": step.expected_outcome}
            success = True
        elif step.action_type == "schedule":
            details = f"Queued reminder: {step.description}"
            changes = {"scheduled": step.description}
            success = True
        elif step.action_type == "analyze":
            details = f"Analyzed state for: {step.description}"
            changes = {"analysis_focus": step.description, "state_snapshot": dict(world_state)}
            success = True
        else:
            details = f"Simulated action: {step.description}"
            changes = {"simulated_action": step.description}
            success = True

        step.status = "completed" if success else "failed"
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
        return ExecutionResult(
            action_id=step.step_id,
            success=success,
            status=step.status,
            details=details,
            observed_changes=changes,
            latency_ms=latency_ms,
        )
