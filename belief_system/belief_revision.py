from __future__ import annotations


class BeliefRevision:
    def revise(self, *, prior: float, posterior: float) -> dict[str, float]:
        return {"delta": round(posterior - prior, 6), "revised_confidence": round(posterior, 6)}
