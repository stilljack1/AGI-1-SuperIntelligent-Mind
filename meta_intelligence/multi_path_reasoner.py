from __future__ import annotations


class MultiPathReasoner:
    def explore(self, hypotheses: list[str], *, confidence: float) -> list[dict[str, object]]:
        paths = []
        for index, hypothesis in enumerate(hypotheses, start=1):
            coherence = max(0.2, min(0.99, confidence - (0.03 * (index - 1)) + 0.02))
            paths.append({"path_id": f"path_{index:02d}", "hypothesis": hypothesis, "coherence": round(coherence, 6)})
        return paths
