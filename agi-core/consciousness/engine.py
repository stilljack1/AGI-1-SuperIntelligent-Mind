from __future__ import annotations

from typing import Any

from runtime.models import ThoughtRecord


class ConsciousnessEngine:
    def __init__(self) -> None:
        self._thought_count = 0

    def generate_thought(
        self,
        *,
        focus: str,
        memory_context: dict[str, list[dict[str, Any]]],
        prediction: dict[str, Any],
        reasoning: dict[str, Any],
    ) -> ThoughtRecord:
        self._thought_count += 1
        uncertainty = round(max(0.0, min(1.0, 1.0 - float(reasoning.get("confidence", 0.5)))), 6)
        rationale = (
            f"Focus={focus}; retrieved={sum(len(items) for items in memory_context.values())} memory items; "
            f"predicted={prediction.get('outcome', 'unknown')}."
        )
        return ThoughtRecord(
            thought_id=f"thought_{self._thought_count:04d}",
            summary=f"Considering {focus}",
            focus=focus,
            rationale=rationale,
            confidence=float(reasoning.get("confidence", 0.5)),
            uncertainty=uncertainty,
            attention_weight=float(reasoning.get("attention_weight", 0.5)),
        )

    def reflect(self, *, thought: ThoughtRecord, self_summary: dict[str, Any]) -> dict[str, Any]:
        limitations = list(self_summary.get("limitations", []))
        reflection = []
        if thought.uncertainty > 0.45:
            reflection.append("uncertainty_high")
        if limitations:
            reflection.append(f"known_limitations={','.join(limitations[:4])}")
        if not reflection:
            reflection.append("thought_within_operating_bounds")
        return {
            "thought_id": thought.thought_id,
            "reflection": reflection,
            "needs_more_evidence": thought.uncertainty > 0.5,
        }
