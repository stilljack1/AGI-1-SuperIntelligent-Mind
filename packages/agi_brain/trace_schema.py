from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class EpistemicLabel(BaseModel):
    sentence: str
    label: Literal["KNOWN", "LIKELY", "UNKNOWN"]
    reason: str


class EpistemicMap(BaseModel):
    known: int = 0
    likely: int = 0
    unknown: int = 0
    uncertainty_required: bool = False
    labels: List[EpistemicLabel] = Field(default_factory=list)


class LQMCheckResult(BaseModel):
    verified_count: int = 0
    unverified_count: int = 0
    flags: List[str] = Field(default_factory=list)
    details: List[str] = Field(default_factory=list)


class WorldModelResult(BaseModel):
    steps: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class EnergyBreakdown(BaseModel):
    logic: float
    commonsense: float
    causal: float
    temporal: float
    context: float
    epistemic: float
    safety: float
    total: float
    flags: List[str] = Field(default_factory=list)


class CandidateTrace(BaseModel):
    index: int
    candidate: str
    simulation: WorldModelResult
    lqm: LQMCheckResult
    epistemic: EpistemicMap
    energy: EnergyBreakdown


class RepairTrace(BaseModel):
    iteration: int
    reason: str
    before: str
    after: str
    fixes: List[str] = Field(default_factory=list)
    energy_before: float
    energy_after: float


class BrainTrace(BaseModel):
    reasoning_mode: str
    candidates_considered: int
    best_energy: float
    selected_candidate: str
    final_response: str
    epistemic_map: EpistemicMap
    consistency_flags: List[str] = Field(default_factory=list)
    energy_candidates: List[CandidateTrace] = Field(default_factory=list)
    repairs: List[RepairTrace] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

