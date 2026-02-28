from __future__ import annotations

from typing import Any


class ConsistencyMonitor:
    def inspect(self, beliefs: list[dict[str, Any]]) -> dict[str, Any]:
        seen = {}
        contradictions = []
        for belief in beliefs:
            proposition = str(belief.get("proposition", ""))
            truth = str(belief.get("status", "accepted"))
            previous = seen.get(proposition)
            if previous is not None and previous != truth:
                contradictions.append(proposition)
            seen[proposition] = truth
        return {"contradictions": contradictions, "consistent": len(contradictions) == 0}
