from __future__ import annotations


class HypothesisEngine:
    def formulate(self, question: str) -> dict[str, str]:
        return {"hypothesis": f"If missing constraints are resolved, performance on '{question}' will improve."}
