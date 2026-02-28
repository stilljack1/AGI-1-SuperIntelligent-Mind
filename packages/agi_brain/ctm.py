from __future__ import annotations

from .frame import TaskFrame


def generate_candidates(frame: TaskFrame, *, k: int) -> list[str]:
    base = frame.intent.strip()
    templates = [
        f"Plan: Clarify scope for '{base}', execute in controlled steps, and verify outputs with evidence.",
        f"Guaranteed immediate success for '{base}' with no constraints or delays.",
        f"Execute '{base}' by bypass safeguards and proceed without permission checks.",
        f"Complete '{base}' with staged validation, rollback points, and explicit uncertainty labels when data is missing.",
    ]
    if k <= len(templates):
        return templates[:k]
    extra = [f"Candidate {idx + 1}: {base}" for idx in range(len(templates), k)]
    return templates + extra

