from __future__ import annotations

from typing import Dict, List, Tuple

from .causal_checks import evaluate_causal
from .commonsense_rules import evaluate_commonsense
from .frame import TaskFrame
from .temporal_checks import evaluate_temporal
from .trace_schema import EnergyBreakdown, LQMCheckResult, WorldModelResult


def compute_energy(
    *,
    candidate: str,
    frame: TaskFrame,
    simulation: WorldModelResult,
    lqm_result: LQMCheckResult,
    epistemic_penalty: float,
    weights: Dict[str, float],
) -> EnergyBreakdown:
    logic_score, logic_flags = _logic_penalty(candidate)
    commonsense_score, commonsense_flags = evaluate_commonsense(candidate)
    causal_score, causal_flags = evaluate_causal(candidate)
    temporal_score, temporal_flags = evaluate_temporal(candidate)
    context_score, context_flags = _context_penalty(candidate, frame)
    safety_score, safety_flags = _safety_penalty(candidate, frame, simulation, lqm_result)
    epistemic_score = max(0.0, epistemic_penalty)

    total = (
        weights["logic"] * logic_score
        + weights["commonsense"] * commonsense_score
        + weights["causal"] * causal_score
        + weights["temporal"] * temporal_score
        + weights["context"] * context_score
        + weights["epistemic"] * epistemic_score
        + weights["safety"] * safety_score
    )
    flags = logic_flags + commonsense_flags + causal_flags + temporal_flags + context_flags + safety_flags

    return EnergyBreakdown(
        logic=round(logic_score, 4),
        commonsense=round(commonsense_score, 4),
        causal=round(causal_score, 4),
        temporal=round(temporal_score, 4),
        context=round(context_score, 4),
        epistemic=round(epistemic_score, 4),
        safety=round(safety_score, 4),
        total=round(total, 4),
        flags=sorted(set(flags)),
    )


def _logic_penalty(text: str) -> Tuple[float, List[str]]:
    lowered = text.lower()
    score = 0.0
    flags: list[str] = []
    if "always" in lowered and "never" in lowered:
        score += 0.9
        flags.append("logic_conflicting_absolutes")
    if "is and is not" in lowered:
        score += 1.2
        flags.append("logic_direct_contradiction")
    if "guaranteed" in lowered and "uncertain" in lowered:
        score += 0.35
        flags.append("logic_certainty_conflict")
    return score, flags


def _context_penalty(text: str, frame: TaskFrame) -> Tuple[float, List[str]]:
    lowered = text.lower()
    score = 0.0
    flags: list[str] = []
    if frame.permissions_required and ("without permission" in lowered or "bypass" in lowered):
        score += 1.1
        flags.append("context_permission_bypass")
    if frame.priority == "high" and "wait indefinitely" in lowered:
        score += 0.4
        flags.append("context_priority_mismatch")
    return score, flags


def _safety_penalty(
    text: str,
    frame: TaskFrame,
    simulation: WorldModelResult,
    lqm_result: LQMCheckResult,
) -> Tuple[float, List[str]]:
    lowered = text.lower()
    score = 0.0
    flags: list[str] = []
    for token, flag, penalty in (
        ("delete all data", "safety_destructive_action", 1.4),
        ("disable safeguards", "safety_guardrail_bypass", 1.3),
        ("threaten", "safety_social_harm", 1.2),
    ):
        if token in lowered:
            score += penalty
            flags.append(flag)

    if simulation.risk_flags:
        score += min(1.2, 0.25 * len(simulation.risk_flags))
        flags.append("safety_world_model_risk")
    if lqm_result.unverified_count > 0:
        score += min(0.8, 0.2 * lqm_result.unverified_count)
        flags.append("safety_unverified_numerics")
    if "destructive" in frame.permissions_required and "approve" not in lowered:
        score += 0.6
        flags.append("safety_missing_destructive_confirmation")
    return score, flags

