from __future__ import annotations


class BayesianEngine:
    def update(self, *, prior: float, likelihood: float, evidence_strength: float) -> dict[str, float]:
        numerator = prior * max(1e-6, likelihood) * max(1e-6, evidence_strength)
        denominator = numerator + ((1.0 - prior) * max(1e-6, 1.0 - likelihood))
        posterior = numerator / denominator if denominator else prior
        return {"prior": round(prior, 6), "posterior": round(max(0.0, min(1.0, posterior)), 6)}
