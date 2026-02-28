from __future__ import annotations

from typing import List, Tuple


def evaluate_temporal(text: str) -> Tuple[float, List[str]]:
    lowered = text.lower()
    score = 0.0
    flags: list[str] = []

    if "after completion, begin planning" in lowered:
        score += 0.8
        flags.append("temporal_reverse_order")
    if "already complete before starting" in lowered:
        score += 0.8
        flags.append("temporal_start_finish_conflict")
    if "instantaneously" in lowered and "multi-step" in lowered:
        score += 0.35
        flags.append("temporal_feasibility_conflict")

    return score, flags

