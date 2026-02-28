from __future__ import annotations


class AnalogyEngine:
    def compare(self, query: str) -> dict[str, str]:
        if "research" in query.lower():
            analogy = "scientific_method"
        elif "build" in query.lower():
            analogy = "systems_engineering_program"
        else:
            analogy = "iterative_control_loop"
        return {"analogy": analogy}
