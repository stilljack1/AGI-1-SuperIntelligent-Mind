from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from runtime.models import FeedbackRecord


class SelfModel:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except Exception:
                pass
        return {
            "identity": "AGI-1",
            "mission": "Persistent autonomous intelligence system",
            "beliefs": ["reason_before_action", "learn_from_feedback", "maintain_truthfulness"],
            "capabilities": [
                "continuous_thinking",
                "unified_memory",
                "planning",
                "feedback_learning",
                "self_reflection",
            ],
            "limitations": ["external_tools_may_be_unavailable", "requires_verified_secrets_for_live_ops"],
            "performance_history": [],
            "current_focus": "bootstrap",
            "self_improvement_backlog": [],
        }

    def update_focus(self, focus: str) -> None:
        self.state["current_focus"] = focus
        self.persist()

    def update_from_feedback(self, feedback: FeedbackRecord, learning_result: dict[str, Any]) -> None:
        history = self.state.setdefault("performance_history", [])
        history.append(
            {
                "feedback_id": feedback.feedback_id,
                "reward": feedback.reward,
                "success": feedback.success,
                "issues": feedback.error_analysis,
            }
        )
        history[:] = history[-200:]
        backlog = self.state.setdefault("self_improvement_backlog", [])
        for improvement in learning_result.get("improvements", []):
            if improvement not in backlog:
                backlog.append(improvement)
        if not feedback.success and "recent_execution_failure" not in self.state["limitations"]:
            self.state["limitations"].append("recent_execution_failure")
        if feedback.success and "recent_execution_failure" in self.state["limitations"]:
            self.state["limitations"].remove("recent_execution_failure")
        self.persist()

    def summary(self) -> dict[str, Any]:
        return {
            "identity": self.state["identity"],
            "mission": self.state["mission"],
            "capabilities": self.state["capabilities"],
            "limitations": self.state["limitations"],
            "current_focus": self.state["current_focus"],
            "performance_entries": len(self.state.get("performance_history", [])),
            "self_improvement_backlog": self.state.get("self_improvement_backlog", []),
        }

    def persist(self) -> None:
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
