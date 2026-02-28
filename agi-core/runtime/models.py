from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Observation:
    cycle_id: int
    timestamp_utc: str
    raw_input: str
    entities: list[str]
    events: list[str]
    inferred_goals: list[str]
    state: dict[str, Any]
    relationships: list[dict[str, Any]]
    importance: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BeliefNode:
    concept: str
    probability: float
    evidence_links: list[str]
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoalRecord:
    goal_id: str
    description: str
    priority: float
    urgency: float
    reward: float
    source: str
    status: str = "active"
    created_at: str = field(default_factory=utc_now)
    due_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThoughtRecord:
    thought_id: str
    summary: str
    focus: str
    rationale: str
    confidence: float
    uncertainty: float
    attention_weight: float
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanStep:
    step_id: str
    description: str
    action_type: str
    expected_outcome: str
    risk: float
    priority: float
    constraints: list[str] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanRecord:
    plan_id: str
    goal_id: str
    strategy: str
    confidence: float
    predicted_success: float
    steps: list[PlanStep]
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload


@dataclass
class ExecutionResult:
    action_id: str
    success: bool
    status: str
    details: str
    observed_changes: dict[str, Any]
    latency_ms: float
    executed_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackRecord:
    feedback_id: str
    action_id: str
    reward: float
    success: bool
    error_analysis: list[str]
    confidence_delta: float
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AGIMessage:
    sender: str
    receiver: str
    intent: str
    data: dict[str, Any]
    confidence: float
    priority: float
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
