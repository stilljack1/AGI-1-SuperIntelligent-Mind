from __future__ import annotations

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any


@dataclass
class ProvenanceConfig:
    cache_path: Path
    history_limit: int = 200

    @classmethod
    def from_env(cls) -> "ProvenanceConfig":
        path = Path(os.getenv("AGI1_REASONING_CACHE_PATH", "runtime/reasoning_trace_cache.json"))
        return cls(cache_path=path, history_limit=max(20, int(os.getenv("AGI1_REASONING_HISTORY_LIMIT", "200"))))


class TraceRepository:
    def __init__(self, config: ProvenanceConfig | None = None) -> None:
        self.config = config or ProvenanceConfig.from_env()
        self.config.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.payload = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config.cache_path.exists():
            return {"cache": {}, "history": []}
        try:
            payload = json.loads(self.config.cache_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload.setdefault("cache", {})
                payload.setdefault("history", [])
                return payload
        except Exception:
            pass
        return {"cache": {}, "history": []}

    def persist(self) -> None:
        self.config.cache_path.write_text(json.dumps(self.payload, indent=2), encoding="utf-8")

    def cache_key(self, *, task_input: str, actor: str, priority: str, mode: str) -> str:
        material = f"{task_input}|{actor}|{priority}|{mode}".encode("utf-8")
        return sha256(material).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        cache = self.payload.get("cache", {})
        item = cache.get(key)
        return item if isinstance(item, dict) else None

    def put(self, *, key: str, trace: dict[str, Any], success: bool, mode: str) -> None:
        self.payload.setdefault("cache", {})[key] = {"trace": trace, "success": success, "mode": mode}
        history = self.payload.setdefault("history", [])
        history.append({"mode": mode, "success": success, "best_energy": trace.get("best_energy", 0.0)})
        history[:] = history[-self.config.history_limit :]
        self.persist()

    def history_score(self, *, mode: str) -> float:
        history = [item for item in self.payload.get("history", []) if item.get("mode") == mode]
        if not history:
            return 0.5
        successes = sum(1 for item in history if item.get("success"))
        return successes / len(history)
