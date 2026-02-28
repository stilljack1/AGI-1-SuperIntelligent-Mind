from __future__ import annotations


class ImaginationScenarioSimulator:
    def simulate(self, query: str) -> list[dict[str, object]]:
        return [
            {"scenario": "expected", "query": query, "confidence": 0.72},
            {"scenario": "optimistic", "query": query, "confidence": 0.58},
            {"scenario": "adverse", "query": query, "confidence": 0.46},
        ]
