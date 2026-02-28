from __future__ import annotations

from typing import Any


class LogicValidator:
    def validate(self, *, query: str, contradictions: list[str], inferences: list[dict[str, Any]]) -> dict[str, Any]:
        valid = len(contradictions) == 0 and len(inferences) > 0 and bool(query.strip())
        return {
            "valid": valid,
            "contradictions": contradictions,
            "inference_count": len(inferences),
        }
