from __future__ import annotations


class ExplorationPolicy:
    def select(self, *, knowledge_gap: float) -> dict[str, object]:
        mode = "explore" if knowledge_gap >= 0.45 else "exploit"
        return {"mode": mode, "exploration_drive": round(max(0.0, min(1.0, knowledge_gap + 0.1)), 6)}
