from __future__ import annotations


class InternalStateMonitor:
    def capture(self, *, confidence: float, uncertainty: float, predicted_success: float) -> dict[str, float]:
        return {
            "confidence_level": round(confidence, 6),
            "uncertainty_level": round(uncertainty, 6),
            "risk_sensitivity": round(1.0 - predicted_success, 6),
            "stability": round((confidence + predicted_success) / 2.0, 6),
            "goal_satisfaction": round(predicted_success, 6),
        }
