from __future__ import annotations


class ConceptCombiner:
    def combine(self, ideas: list[str]) -> dict[str, str]:
        return {"combined_concept": " + ".join(ideas[:2]) if ideas else "none"}
