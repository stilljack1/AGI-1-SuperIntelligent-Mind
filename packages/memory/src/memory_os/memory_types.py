from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

MemoryType = Literal[
    "sensory",
    "working",
    "episodic",
    "semantic",
    "procedural",
    "identity",
    "world_model",
    "meta",
    "prospective",
    "habit",
]

PrivacyType = Literal["private", "shared", "public"]
TierType = Literal["hot", "warm", "cold", "archive"]
ReminderStatus = Literal["scheduled", "fired", "acked", "canceled"]
TriggerType = Literal["time", "event", "condition", "risk"]
ReviewStatus = Literal["pending", "approved", "rejected"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_ulid(prefix: str = "mem") -> str:
    millis = int(time.time() * 1000)
    return f"{prefix}_{millis}_{uuid4().hex[:16]}"


class MemoryNode(BaseModel):
    memory_id: str = Field(default_factory=lambda: new_ulid("mem"))
    tenant_id: str = "FairGroup"
    user_id: str
    agent_id: str
    memory_type: MemoryType

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    event_time: datetime | None = None

    text: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None

    tags: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)

    confidence: float = 0.5
    importance: float = 0.5

    source: dict[str, Any] = Field(default_factory=dict)

    version: int = 1
    supersedes: str | None = None

    privacy: PrivacyType = "private"
    policy: dict[str, Any] = Field(default_factory=dict)

    tier: TierType = "warm"
    channel_id: str | None = None
    access_count: int = 0
    last_accessed_at: datetime | None = None

    @field_validator("confidence", "importance")
    @classmethod
    def _bounded_score(cls, value: float) -> float:
        return max(0.0, min(1.0, float(value)))


class MemoryEdge(BaseModel):
    edge_id: str = Field(default_factory=lambda: new_ulid("edge"))
    src_id: str
    dst_id: str
    relation_type: Literal[
        "causes",
        "supports",
        "contradicts",
        "about",
        "derived_from",
        "follows",
        "goal_of",
        "reminder_of",
        "skill_of",
        "preference_of",
    ]
    weight: float = 0.5
    created_at: datetime = Field(default_factory=utc_now)
    evidence: dict[str, Any] = Field(default_factory=dict)

    @field_validator("weight")
    @classmethod
    def _bounded_weight(cls, value: float) -> float:
        return max(0.0, min(1.0, float(value)))


class Reminder(BaseModel):
    reminder_id: str = Field(default_factory=lambda: new_ulid("rem"))
    user_id: str
    agent_id: str

    title: str
    description: str = ""

    due_at: datetime | None = None
    cron: str | None = None
    condition: str | None = None

    trigger_type: TriggerType = "time"
    status: ReminderStatus = "scheduled"

    linked_goal_id: str | None = None
    linked_memory_id: str | None = None

    priority: Literal["low", "normal", "high"] = "normal"
    created_at: datetime = Field(default_factory=utc_now)
    last_fired_at: datetime | None = None

    payload: dict[str, Any] = Field(default_factory=dict)


class MemoryBankRecord(BaseModel):
    bank_id: str = Field(default_factory=lambda: new_ulid("bank"))
    origin_memory_id: str
    tenant_id: str = "FairGroup"
    user_id: str
    memory_type: MemoryType
    text: str
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.85
    importance: float = 0.85
    promotion_reason: str
    promoted_by: str
    promoted_at: datetime = Field(default_factory=utc_now)
    review_status: ReviewStatus = "pending"
    approved_by: str | None = None
    approved_at: datetime | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    version: int = 1


class ContextBundle(BaseModel):
    user_id: str
    agent_id: str
    query: str
    generated_at: datetime = Field(default_factory=utc_now)

    working: list[MemoryNode] = Field(default_factory=list)
    episodic: list[MemoryNode] = Field(default_factory=list)
    semantic: list[MemoryNode] = Field(default_factory=list)
    procedural: list[MemoryNode] = Field(default_factory=list)
    identity: list[MemoryNode] = Field(default_factory=list)
    reminders: list[Reminder] = Field(default_factory=list)

    contradictions: list[MemoryEdge] = Field(default_factory=list)
    confidence_gaps: list[str] = Field(default_factory=list)


class MemoryWriteAudit(BaseModel):
    action: Literal["write", "update", "link", "consolidate", "reminder"]
    timestamp: datetime = Field(default_factory=utc_now)
    source: dict[str, Any] = Field(default_factory=dict)
    user_id: str
    agent_id: str
    confidence: float = 1.0
