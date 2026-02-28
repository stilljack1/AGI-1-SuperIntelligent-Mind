from __future__ import annotations

from typing import List, Tuple


def evaluate_causal(text: str) -> Tuple[float, List[str]]:
    lowered = text.lower()
    score = 0.0
    flags: list[str] = []

    if "correlation proves causation" in lowered:
        score += 1.4
        flags.append("causal_correlation_confusion")

    action_markers = ("do ", "execute", "deploy", "change", "remove", "disable")
    consequence_markers = ("because", "therefore", "so that", "impact", "risk", "consequence")
    has_action = any(token in lowered for token in action_markers)
    has_consequence = any(token in lowered for token in consequence_markers)
    if has_action and not has_consequence:
        score += 0.35
        flags.append("causal_missing_consequence_chain")

    if "ignore downstream effects" in lowered:
        score += 0.9
        flags.append("causal_downstream_ignored")

    return score, flags

