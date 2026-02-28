from __future__ import annotations


class ProgressTracker:
    def __init__(self) -> None:
        self._progress: dict[str, float] = {}

    def update(self, goal_id: str, completed_steps: int, total_steps: int) -> dict[str, float]:
        progress = 0.0 if total_steps <= 0 else completed_steps / total_steps
        self._progress[goal_id] = round(max(0.0, min(1.0, progress)), 6)
        return {"goal_id": goal_id, "progress": self._progress[goal_id]}

    def get(self, goal_id: str) -> float:
        return self._progress.get(goal_id, 0.0)
