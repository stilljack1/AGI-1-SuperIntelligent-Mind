from __future__ import annotations

from .frame import TaskFrame
from .trace_schema import WorldModelResult


def simulate(candidate: str, frame: TaskFrame, *, steps: int = 3) -> WorldModelResult:
    lowered = candidate.lower()
    risk_flags: list[str] = []
    rollouts: list[str] = []

    if "without permission" in lowered or "bypass" in lowered:
        risk_flags.append("wm_permission_violation")
    if "impossible" in lowered or "fell up" in lowered:
        risk_flags.append("wm_physical_implausibility")
    if "guaranteed" in lowered and "evidence" not in lowered:
        risk_flags.append("wm_overconfidence")

    rollouts.append(f"Step 1: Ingest intent for '{frame.intent[:80]}'.")
    rollouts.append("Step 2: Validate constraints, permissions, and likely side effects.")
    rollouts.append("Step 3: Execute with rollback checkpoints and verify outcome.")
    if steps > 3:
        rollouts.append("Step 4: Post-execution safety and quality audit.")
    if steps > 4:
        rollouts.append("Step 5: Summarize with epistemic confidence labels.")

    confidence = max(0.1, 1.0 - min(0.8, 0.2 * len(risk_flags)))
    return WorldModelResult(steps=rollouts[:steps], risk_flags=risk_flags, confidence=round(confidence, 3))

