from __future__ import annotations


class PerformanceAnalyzer:
    def __init__(self) -> None:
        self.history: list[float] = []

    def update(self, reward: float) -> dict[str, float]:
        self.history.append(reward)
        self.history[:] = self.history[-50:]
        average = sum(self.history) / len(self.history)
        return {"recent_average_reward": round(average, 6), "sample_count": float(len(self.history))}
