from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Vote:
    supervisor_id: str
    approve: bool
    weight: float = 1.0


class ConsensusEngine:
    def __init__(self, threshold: float = 0.67) -> None:
        self.threshold = threshold

    def evaluate(self, votes: Iterable[Vote]) -> dict[str, float | bool]:
        votes = list(votes)
        if not votes:
            return {"approved": False, "approval_ratio": 0.0}
        weighted_total = sum(v.weight for v in votes)
        weighted_approve = sum(v.weight for v in votes if v.approve)
        ratio = weighted_approve / weighted_total if weighted_total else 0.0
        return {"approved": ratio >= self.threshold, "approval_ratio": ratio}

