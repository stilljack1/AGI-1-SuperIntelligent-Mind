from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b
from pathlib import Path

from .stores.sqlite_store import SQLiteMemoryStore


@dataclass(frozen=True)
class ShardDescriptor:
    index: int
    db_path: str


class ShardManager:
    def __init__(self, *, base_db_path: str | Path, shard_count: int = 1) -> None:
        self.base_db_path = Path(base_db_path)
        self.shard_count = max(1, int(shard_count))
        self._stores: list[SQLiteMemoryStore] = []
        self._descriptors: list[ShardDescriptor] = []

        if self.shard_count == 1:
            self._stores.append(SQLiteMemoryStore(self.base_db_path))
            self._descriptors.append(ShardDescriptor(index=0, db_path=str(self.base_db_path)))
        else:
            stem = self.base_db_path.stem
            suffix = self.base_db_path.suffix or ".sqlite"
            for idx in range(self.shard_count):
                shard_path = self.base_db_path.with_name(f"{stem}_shard_{idx}{suffix}")
                self._stores.append(SQLiteMemoryStore(shard_path))
                self._descriptors.append(ShardDescriptor(index=idx, db_path=str(shard_path)))

    def shard_index(self, user_id: str, memory_type: str) -> int:
        if self.shard_count == 1:
            return 0
        digest = blake2b(f"{user_id}:{memory_type}".encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        return value % self.shard_count

    def store_for(self, *, user_id: str, memory_type: str) -> SQLiteMemoryStore:
        return self._stores[self.shard_index(user_id, memory_type)]

    def all_stores(self) -> list[SQLiteMemoryStore]:
        return list(self._stores)

    def descriptors(self) -> list[ShardDescriptor]:
        return list(self._descriptors)
