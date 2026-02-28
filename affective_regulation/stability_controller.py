from __future__ import annotations


class StabilityController:
    def advise(self, *, stability: float, uncertainty: float) -> dict[str, object]:
        if stability < 0.45 or uncertainty > 0.55:
            posture = "stabilize"
        else:
            posture = "advance"
        return {"posture": posture}
