from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnergyDecision:
    relevance: float
    urgency: float
    reward: float
    importance: float


class EnergyAllocator:
    """Allocate attention according to relevance x urgency x reward."""

    def score(self, *, relevance: float, urgency: float, reward: float) -> EnergyDecision:
        rel = max(0.0, min(1.0, relevance))
        urg = max(0.0, min(1.0, urgency))
        rew = max(0.0, min(1.0, reward))
        importance = round(rel * urg * rew, 6)
        return EnergyDecision(relevance=rel, urgency=urg, reward=rew, importance=importance)

    def allocate(self, items: list[dict[str, float]]) -> list[dict[str, float]]:
        ranked = []
        for item in items:
            decision = self.score(
                relevance=float(item.get("relevance", 0.5)),
                urgency=float(item.get("urgency", 0.5)),
                reward=float(item.get("reward", 0.5)),
            )
            ranked.append({**item, "importance": decision.importance})
        return sorted(ranked, key=lambda row: row["importance"], reverse=True)
