from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    size: int


class L1Cache:
    def __init__(self, capacity: int = 256) -> None:
        self.capacity = max(16, int(capacity))
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            self._misses += 1
            return None
        self._hits += 1
        value = self._store.pop(key)
        self._store[key] = value
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        while len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> CacheStats:
        return CacheStats(hits=self._hits, misses=self._misses, size=len(self._store))
