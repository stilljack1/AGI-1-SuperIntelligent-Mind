from __future__ import annotations


class ExperimentPlanner:
    def plan(self, hypothesis: str) -> dict[str, object]:
        return {
            "experiment": "compare baseline and improved strategies",
            "hypothesis": hypothesis,
            "metrics": ["reward", "alignment_score", "stability"],
        }
