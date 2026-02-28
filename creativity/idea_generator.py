from __future__ import annotations


class IdeaGenerator:
    def generate(self, query: str) -> list[str]:
        return [
            f"modularize::{query}",
            f"simulate::{query}",
            f"measure::{query}",
        ]
