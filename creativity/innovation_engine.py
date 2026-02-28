from __future__ import annotations

from typing import Any


class InnovationEngine:
    def synthesize(self, concept: dict[str, Any], *, novelty_score: float) -> dict[str, Any]:
        return {
            "proposal": f"innovation::{concept.get('combined_concept', 'none')}",
            "creativity_score": round(max(0.0, min(1.0, novelty_score + 0.15)), 6),
        }
