from __future__ import annotations


class KnowledgeGapAnalyzer:
    def analyze(self, *, uncertainty: float, novelty_score: float) -> dict[str, float]:
        gap = max(0.0, min(1.0, (0.6 * uncertainty) + (0.4 * novelty_score)))
        return {"knowledge_gap": round(gap, 6)}
