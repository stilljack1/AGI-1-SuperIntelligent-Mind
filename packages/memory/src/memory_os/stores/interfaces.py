from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ..memory_types import MemoryBankRecord, MemoryEdge, MemoryNode, Reminder


class DocStore(ABC):
    @abstractmethod
    def write_node(self, node: MemoryNode, expected_version: int | None = None) -> MemoryNode:
        raise NotImplementedError

    @abstractmethod
    def get_current(self, memory_id: str) -> MemoryNode | None:
        raise NotImplementedError

    @abstractmethod
    def get_many(self, memory_ids: list[str]) -> list[MemoryNode]:
        raise NotImplementedError

    @abstractmethod
    def query_nodes(
        self,
        *,
        user_id: str,
        memory_types: list[str] | None = None,
        tier: str | None = None,
        include_archived: bool = False,
    ) -> list[MemoryNode]:
        raise NotImplementedError

    @abstractmethod
    def update_access(self, memory_ids: list[str], accessed_at: datetime) -> None:
        raise NotImplementedError


class VectorStore(ABC):
    @abstractmethod
    def semantic_search(
        self,
        *,
        query_embedding: list[float],
        user_id: str,
        memory_types: list[str] | None = None,
        top_k: int = 20,
        tier: str | None = None,
    ) -> list[tuple[MemoryNode, float]]:
        raise NotImplementedError


class GraphStore(ABC):
    @abstractmethod
    def write_edge(self, edge: MemoryEdge) -> MemoryEdge:
        raise NotImplementedError

    @abstractmethod
    def edges_for_node(self, memory_id: str) -> list[MemoryEdge]:
        raise NotImplementedError


class EventStore(ABC):
    @abstractmethod
    def list_since(self, *, user_id: str, since: datetime, limit: int = 200) -> list[MemoryNode]:
        raise NotImplementedError


class ReminderStore(ABC):
    @abstractmethod
    def create_reminder(self, reminder: Reminder) -> Reminder:
        raise NotImplementedError

    @abstractmethod
    def due_reminders(self, *, now: datetime, user_id: str, limit: int = 50) -> list[Reminder]:
        raise NotImplementedError

    @abstractmethod
    def ack_reminder(self, reminder_id: str, *, status: str = "acked") -> Reminder | None:
        raise NotImplementedError


class MemoryBankStore(ABC):
    @abstractmethod
    def upsert_bank_record(self, record: MemoryBankRecord) -> MemoryBankRecord:
        raise NotImplementedError

    @abstractmethod
    def query_bank(self, *, user_id: str, query: str, top_k: int = 20) -> list[MemoryBankRecord]:
        raise NotImplementedError

    @abstractmethod
    def review_bank_record(self, bank_id: str, *, status: str, reviewer: str) -> MemoryBankRecord | None:
        raise NotImplementedError
