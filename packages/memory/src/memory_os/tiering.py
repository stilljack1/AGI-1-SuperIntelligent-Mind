from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from .memory_types import MemoryNode, utc_now


@dataclass(frozen=True)
class TierPolicy:
    hot_threshold: float = 0.72
    warm_threshold: float = 0.38
    archive_days: int = 90


def _hours_since(value: datetime | None, now: datetime) -> float:
    if value is None:
        return 24.0
    ref = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    delta = now - ref
    return max(0.0, delta.total_seconds() / 3600.0)


def score_hotness(node: MemoryNode, now: datetime | None = None) -> float:
    now = now or utc_now()
    age_hours = _hours_since(node.updated_at, now)
    recency = math.exp(-0.08 * age_hours)
    access = 1.0 - math.exp(-0.2 * float(node.access_count))
    relevance = float(node.payload.get("goal_relevance", 0.5)) if isinstance(node.payload, dict) else 0.5
    score = (0.35 * recency) + (0.25 * access) + (0.25 * node.importance) + (0.15 * relevance)
    return max(0.0, min(1.0, score))


class TierManager:
    def __init__(self, policy: TierPolicy | None = None) -> None:
        self.policy = policy or TierPolicy()

    def target_tier(self, node: MemoryNode, now: datetime | None = None) -> str:
        now = now or utc_now()
        age_days = _hours_since(node.updated_at, now) / 24.0
        if age_days >= self.policy.archive_days:
            return "archive"

        score = score_hotness(node, now)
        if score >= self.policy.hot_threshold:
            return "hot"
        if score >= self.policy.warm_threshold:
            return "warm"
        return "cold"

    def migrate_plan(self, nodes: list[MemoryNode], now: datetime | None = None) -> dict[str, list[str]]:
        now = now or utc_now()
        updates: dict[str, list[str]] = {"hot": [], "warm": [], "cold": [], "archive": []}
        for node in nodes:
            next_tier = self.target_tier(node, now=now)
            if node.tier != next_tier:
                updates[next_tier].append(node.memory_id)
        return updates
