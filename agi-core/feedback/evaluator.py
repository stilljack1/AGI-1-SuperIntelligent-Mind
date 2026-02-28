from __future__ import annotations

from runtime.models import ExecutionResult, FeedbackRecord, PlanRecord


class FeedbackEvaluator:
    def __init__(self) -> None:
        self._feedback_count = 0

    def evaluate(self, *, plan: PlanRecord, result: ExecutionResult, predicted_success: float) -> FeedbackRecord:
        self._feedback_count += 1
        success = bool(result.success)
        reward = (1.0 if success else -1.0) * max(0.1, predicted_success)
        issues = []
        if not success:
            issues.append("execution_failed")
        if result.latency_ms > 1200:
            issues.append("latency_high")
        if predicted_success < 0.5:
            issues.append("confidence_low")
        return FeedbackRecord(
            feedback_id=f"feedback_{self._feedback_count:04d}",
            action_id=result.action_id,
            reward=round(reward, 6),
            success=success,
            error_analysis=issues,
            confidence_delta=round((0.08 if success else -0.12) * predicted_success, 6),
        )
