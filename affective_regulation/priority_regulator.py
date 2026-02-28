from __future__ import annotations


class PriorityRegulator:
    def regulate(self, *, urgency: float, risk_sensitivity: float, exploration_drive: float) -> dict[str, float]:
        priority = (0.5 * urgency) + (0.25 * (1.0 - risk_sensitivity)) + (0.25 * exploration_drive)
        return {"regulated_priority": round(max(0.0, min(1.0, priority)), 6)}
