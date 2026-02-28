from __future__ import annotations


class QuestionGenerator:
    def generate(self, query: str) -> dict[str, str]:
        return {"research_question": f"What evidence would most improve success on: {query}?"}
