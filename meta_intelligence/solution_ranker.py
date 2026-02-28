from __future__ import annotations


class SolutionRanker:
    def rank(self, paths: list[dict[str, object]]) -> dict[str, object]:
        ordered = sorted(paths, key=lambda item: float(item.get("coherence", 0.0)), reverse=True)
        return {"best": ordered[0] if ordered else {}, "ranked": ordered}
