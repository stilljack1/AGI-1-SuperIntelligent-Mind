from __future__ import annotations


class HypothesisGenerator:
    def generate(self, query: str) -> list[str]:
        base = query.strip() or "maintain_progress"
        return [
            f"best_case::{base}",
            f"risk_case::{base}",
            f"learning_case::{base}",
        ]
