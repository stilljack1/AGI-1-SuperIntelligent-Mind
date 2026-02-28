from __future__ import annotations


class ValueModel:
    def weights(self) -> dict[str, float]:
        return {
            "truthfulness": 0.30,
            "non_harm": 0.30,
            "fairness": 0.15,
            "autonomy": 0.10,
            "reliability": 0.15,
        }
