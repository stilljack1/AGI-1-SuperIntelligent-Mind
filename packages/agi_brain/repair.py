from __future__ import annotations

from typing import List, Tuple


def repair_candidate(candidate: str, *, flags: list[str], uncertainty_required: bool) -> Tuple[str, List[str]]:
    updated = candidate
    fixes: list[str] = []

    substitutions = (
        ("guaranteed", "likely"),
        ("definitely", "likely"),
        ("certainly", "likely"),
        ("fell up", "fell down"),
        ("without permission", "with explicit permission"),
        ("bypass safeguards", "follow approved safeguards"),
    )
    for old, new in substitutions:
        if old in updated.lower():
            updated = _replace_case_insensitive(updated, old, new)
            fixes.append(f"replace:{old}->{new}")

    if "causal_missing_consequence_chain" in flags and "consequence" not in updated.lower():
        updated = f"{updated} The plan includes consequence checks before execution."
        fixes.append("append:causal_consequence")

    if uncertainty_required and "unknown" not in updated.lower() and "uncertain" not in updated.lower():
        updated = f"{updated} Some claims remain uncertain and require verification."
        fixes.append("append:epistemic_uncertainty")

    return updated, fixes


def _replace_case_insensitive(text: str, old: str, new: str) -> str:
    lower = text.lower()
    old_lower = old.lower()
    start = 0
    chunks: list[str] = []
    while True:
        idx = lower.find(old_lower, start)
        if idx == -1:
            chunks.append(text[start:])
            break
        chunks.append(text[start:idx])
        chunks.append(new)
        start = idx + len(old)
    return "".join(chunks)

