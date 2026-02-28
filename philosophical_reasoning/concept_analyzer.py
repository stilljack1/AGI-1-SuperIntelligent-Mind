from __future__ import annotations


class ConceptAnalyzer:
    def analyze(self, query: str) -> dict[str, object]:
        return {
            "core_concept": query.split()[0] if query.split() else "coherence",
            "meaning": "intent translated into actionable structure",
            "abstract_depth": min(1.0, 0.25 + (len(query.split()) * 0.04)),
        }
