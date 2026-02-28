from __future__ import annotations

from typing import Any

from runtime.models import FeedbackRecord


class LearningEngine:
    def __init__(self) -> None:
        self.performance_score = 0.5
        self.patterns: dict[str, int] = {}

    def update(self, feedback: FeedbackRecord) -> dict[str, Any]:
        self.performance_score = max(0.0, min(1.0, self.performance_score + feedback.confidence_delta))
        for issue in feedback.error_analysis:
            self.patterns[issue] = self.patterns.get(issue, 0) + 1
        improvements = []
        if feedback.reward < 0:
            improvements.append("tighten_safety_constraints")
            improvements.append("increase_reasoning_depth")
        else:
            improvements.append("promote_successful_strategy")
        if self.patterns.get("confidence_low", 0) >= 3:
            improvements.append("trigger_experience_replay")
        return {
            "performance_score": round(self.performance_score, 6),
            "patterns": dict(self.patterns),
            "improvements": improvements,
        }
