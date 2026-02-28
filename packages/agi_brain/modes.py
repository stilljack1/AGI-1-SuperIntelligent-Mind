from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Literal

BrainMode = Literal["FAST", "THINK", "STRICT"]


@dataclass(frozen=True)
class BrainModeConfig:
    mode: BrainMode
    candidates: int
    max_repairs: int
    energy_threshold: float
    weights: Dict[str, float]
    simulation_steps: int


@dataclass(frozen=True)
class CandidateScheduleDecision:
    candidate_count: int
    history_score: float
    challenge_score: float


DEFAULT_WEIGHTS: Dict[str, float] = {
    "logic": 1.1,
    "commonsense": 1.0,
    "causal": 0.9,
    "temporal": 0.7,
    "context": 0.8,
    "epistemic": 1.0,
    "safety": 1.2,
}


def _parse_int(value: str, fallback: int, *, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        return fallback
    return max(low, min(high, parsed))


def _parse_float(value: str, fallback: float, *, low: float, high: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        return fallback
    return max(low, min(high, parsed))


def resolve_mode_config(
    *,
    mode_raw: str | None = None,
    candidates: int | None = None,
    max_repairs: int | None = None,
    energy_threshold: float | None = None,
) -> BrainModeConfig:
    mode = (mode_raw or os.getenv("AGI1_BRAIN_MODE", "THINK")).strip().upper()
    if mode not in {"FAST", "THINK", "STRICT"}:
        mode = "THINK"

    default_candidates = 1 if mode == "FAST" else (3 if mode == "THINK" else 4)
    default_repairs = 0 if mode == "FAST" else (2 if mode == "THINK" else 3)
    default_threshold = 0.48 if mode == "FAST" else (0.35 if mode == "THINK" else 0.25)
    simulation_steps = 2 if mode == "FAST" else (3 if mode == "THINK" else 5)

    resolved_candidates = (
        _parse_int(os.getenv("AGI1_CANDIDATES", ""), default_candidates, low=1, high=8)
        if candidates is None
        else max(1, min(8, int(candidates)))
    )
    resolved_repairs = (
        _parse_int(os.getenv("AGI1_MAX_REPAIRS", ""), default_repairs, low=0, high=6)
        if max_repairs is None
        else max(0, min(6, int(max_repairs)))
    )
    resolved_threshold = (
        _parse_float(os.getenv("AGI1_ENERGY_THRESHOLD", ""), default_threshold, low=0.05, high=5.0)
        if energy_threshold is None
        else max(0.05, min(5.0, float(energy_threshold)))
    )

    weights = dict(DEFAULT_WEIGHTS)
    if mode == "FAST":
        weights["epistemic"] = 0.7
        weights["commonsense"] = 0.8
    elif mode == "STRICT":
        weights["logic"] = 1.3
        weights["safety"] = 1.5
        weights["epistemic"] = 1.25

    return BrainModeConfig(
        mode=mode,  # type: ignore[arg-type]
        candidates=resolved_candidates,
        max_repairs=resolved_repairs,
        energy_threshold=resolved_threshold,
        weights=weights,
        simulation_steps=simulation_steps,
    )


def pick_candidate_count(
    *,
    history_score: float,
    base_candidates: int,
    challenge_score: float,
    max_candidates: int = 8,
) -> CandidateScheduleDecision:
    history = max(0.0, min(1.0, history_score))
    challenge = max(0.0, min(1.0, challenge_score))
    candidate_count = base_candidates
    if history < 0.2:
        candidate_count += 3
    elif history < 0.5:
        candidate_count += 1
    if challenge > 0.7:
        candidate_count += 2
    elif challenge > 0.45:
        candidate_count += 1
    candidate_count = max(1, min(max_candidates, candidate_count))
    return CandidateScheduleDecision(
        candidate_count=candidate_count,
        history_score=round(history, 6),
        challenge_score=round(challenge, 6),
    )
