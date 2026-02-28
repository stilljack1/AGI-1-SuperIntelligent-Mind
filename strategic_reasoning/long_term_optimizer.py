from __future__ import annotations


class LongTermOptimizer:
    def optimize(self, scenarios: list[dict[str, float]]) -> dict[str, object]:
        scored = []
        for scenario in scenarios:
            score = float(scenario["reward"]) - (0.7 * float(scenario["risk"])) + (0.03 * float(scenario["horizon"]))
            enriched = dict(scenario)
            enriched["score"] = round(score, 6)
            scored.append(enriched)
        scored.sort(key=lambda item: float(item["score"]), reverse=True)
        return {"best": scored[0] if scored else {}, "ranked": scored}
