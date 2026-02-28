from __future__ import annotations


class EpistemologyEngine:
    def evaluate(self, *, evidence_count: int, uncertainty: float) -> dict[str, object]:
        confidence_band = "high" if uncertainty < 0.2 else ("medium" if uncertainty < 0.45 else "low")
        return {
            "evidence_count": evidence_count,
            "uncertainty": round(uncertainty, 6),
            "confidence_band": confidence_band,
        }
