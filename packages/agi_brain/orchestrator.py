from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .ctm import generate_candidates
from .energy import compute_energy
from .epistemic import analyze_epistemics
from .frame import TaskFrame, build_frame
from .lqm_tools import verify_numbers
from .modes import BrainModeConfig, pick_candidate_count, resolve_mode_config
from .provenance import TraceRepository
from .repair import repair_candidate
from .trace_schema import BrainTrace, CandidateTrace, RepairTrace
from .world_model_lite import simulate


@dataclass
class BrainResult:
    final_response: str
    trace: BrainTrace


class BrainOrchestrator:
    def __init__(self, mode_config: BrainModeConfig) -> None:
        self._config = mode_config

    @classmethod
    def from_settings(
        cls,
        *,
        mode: str,
        candidates: int,
        max_repairs: int,
        energy_threshold: float,
    ) -> "BrainOrchestrator":
        config = resolve_mode_config(
            mode_raw=mode,
            candidates=candidates,
            max_repairs=max_repairs,
            energy_threshold=energy_threshold,
        )
        return cls(config)

    def run(
        self,
        *,
        task_input: str,
        actor: str,
        priority: str,
        mode: str,
        context: Dict[str, Any] | None = None,
    ) -> BrainResult:
        frame = build_frame(user_message=task_input, actor=actor, priority=priority, mode=mode)
        repository = TraceRepository()
        cache_key = repository.cache_key(task_input=task_input, actor=actor, priority=priority, mode=mode)
        cached = repository.get(cache_key)
        if cached and isinstance(cached.get("trace"), dict):
            trace = BrainTrace.model_validate(cached["trace"])
            return BrainResult(final_response=trace.final_response, trace=trace)

        challenge_score = max(0.0, min(1.0, (len(task_input) / 320.0) + (len(str(context or {})) / 800.0)))
        schedule = pick_candidate_count(
            history_score=repository.history_score(mode=self._config.mode),
            base_candidates=self._config.candidates,
            challenge_score=challenge_score,
        )
        candidate_texts = generate_candidates(frame, k=schedule.candidate_count)
        candidate_traces: list[CandidateTrace] = []

        best_index = -1
        best_energy = float("inf")
        best_text = ""
        best_epistemic = None
        best_flags: list[str] = []
        best_trace: CandidateTrace | None = None

        for index, candidate in enumerate(candidate_texts):
            simulation = simulate(candidate, frame, steps=self._config.simulation_steps)
            lqm = verify_numbers(candidate)
            epistemic, epistemic_penalty = analyze_epistemics(candidate)
            energy = compute_energy(
                candidate=candidate,
                frame=frame,
                simulation=simulation,
                lqm_result=lqm,
                epistemic_penalty=epistemic_penalty,
                weights=self._config.weights,
            )
            trace = CandidateTrace(
                index=index,
                candidate=candidate,
                simulation=simulation,
                lqm=lqm,
                epistemic=epistemic,
                energy=energy,
            )
            candidate_traces.append(trace)
            if energy.total < best_energy:
                best_energy = energy.total
                best_index = index
                best_text = candidate
                best_epistemic = epistemic
                best_flags = list(energy.flags)
                best_trace = trace

        if best_epistemic is None or best_trace is None:
            best_epistemic, _ = analyze_epistemics(task_input)
            best_trace = candidate_traces[0] if candidate_traces else None

        repairs: list[RepairTrace] = []
        current_text = best_text
        current_energy = best_energy
        current_epistemic = best_epistemic
        current_flags = list(best_flags)

        for iteration in range(self._config.max_repairs):
            if current_energy <= self._config.energy_threshold:
                break
            repaired, fixes = repair_candidate(
                current_text,
                flags=current_flags,
                uncertainty_required=current_epistemic.uncertainty_required,
            )
            if repaired == current_text:
                break
            repaired_sim = simulate(repaired, frame, steps=self._config.simulation_steps)
            repaired_lqm = verify_numbers(repaired)
            repaired_epi, repaired_epi_penalty = analyze_epistemics(repaired)
            repaired_energy = compute_energy(
                candidate=repaired,
                frame=frame,
                simulation=repaired_sim,
                lqm_result=repaired_lqm,
                epistemic_penalty=repaired_epi_penalty,
                weights=self._config.weights,
            )
            repairs.append(
                RepairTrace(
                    iteration=iteration + 1,
                    reason="energy_above_threshold",
                    before=current_text,
                    after=repaired,
                    fixes=fixes,
                    energy_before=current_energy,
                    energy_after=repaired_energy.total,
                )
            )
            current_text = repaired
            current_energy = repaired_energy.total
            current_epistemic = repaired_epi
            current_flags = repaired_energy.flags

        final_response = current_text
        if current_epistemic.uncertainty_required and "uncertain" not in final_response.lower():
            final_response = f"{final_response} Some elements remain uncertain and should be verified."

        trace = BrainTrace(
            reasoning_mode=self._config.mode,
            candidates_considered=len(candidate_texts),
            best_energy=round(current_energy, 4),
            selected_candidate=final_response,
            final_response=final_response,
            epistemic_map=current_epistemic,
            consistency_flags=sorted(set(current_flags)),
            energy_candidates=candidate_traces,
            repairs=repairs,
            metadata={
                "actor": actor,
                "priority": priority,
                "mode": mode,
                "threshold": str(self._config.energy_threshold),
                "history_score": str(schedule.history_score),
                "challenge_score": str(schedule.challenge_score),
            },
        )
        repository.put(
            key=cache_key,
            trace=trace.model_dump(mode="json"),
            success=current_energy <= self._config.energy_threshold,
            mode=self._config.mode,
        )
        return BrainResult(final_response=final_response, trace=trace)
