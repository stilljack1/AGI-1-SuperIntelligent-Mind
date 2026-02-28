from __future__ import annotations

import re
from typing import List

from .trace_schema import EpistemicLabel, EpistemicMap

CERTAINTY_TOKENS = ("guaranteed", "definitely", "certainly", "always", "never fails", "proven")
EVIDENCE_TOKENS = ("according to", "based on data", "source:", "measured", "observed", "evidence")


def _split_sentences(text: str) -> List[str]:
    parts = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return parts if parts else [text.strip()]


def analyze_epistemics(text: str) -> tuple[EpistemicMap, float]:
    labels: list[EpistemicLabel] = []
    known = likely = unknown = 0
    penalty = 0.0

    for sentence in _split_sentences(text):
        lowered = sentence.lower()
        has_certainty = any(token in lowered for token in CERTAINTY_TOKENS)
        has_evidence = any(token in lowered for token in EVIDENCE_TOKENS)
        if has_certainty and not has_evidence:
            unknown += 1
            penalty += 0.45
            labels.append(EpistemicLabel(sentence=sentence, label="UNKNOWN", reason="certainty_without_evidence"))
        elif has_evidence:
            known += 1
            labels.append(EpistemicLabel(sentence=sentence, label="KNOWN", reason="contains_evidence_marker"))
        else:
            likely += 1
            penalty += 0.08
            labels.append(EpistemicLabel(sentence=sentence, label="LIKELY", reason="no_strong_evidence_marker"))

    result = EpistemicMap(
        known=known,
        likely=likely,
        unknown=unknown,
        uncertainty_required=unknown > 0,
        labels=labels,
    )
    return result, penalty

