from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BeliefStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.beliefs = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def upsert(self, *, proposition: str, confidence: float, evidence: list[str], status: str = "accepted") -> dict[str, Any]:
        belief = {
            "proposition": proposition,
            "confidence": round(max(0.0, min(1.0, confidence)), 6),
            "evidence": evidence,
            "status": status,
        }
        self.beliefs = [belief] + [item for item in self.beliefs if item.get("proposition") != proposition]
        self.beliefs[:] = self.beliefs[:200]
        self.persist()
        return belief

    def all(self) -> list[dict[str, Any]]:
        return list(self.beliefs)

    def persist(self) -> None:
        self.path.write_text(json.dumps(self.beliefs, indent=2), encoding="utf-8")
