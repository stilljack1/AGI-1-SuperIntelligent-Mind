from __future__ import annotations

from .memory_types import MemoryBankRecord
from .stores.interfaces import DocStore, GraphStore, MemoryBankStore


class MemoryBankService:
    def __init__(self, *, doc_store: DocStore, graph_store: GraphStore, bank_store: MemoryBankStore) -> None:
        self.doc_store = doc_store
        self.graph_store = graph_store
        self.bank_store = bank_store

    def promote_to_bank(
        self,
        *,
        memory_id: str,
        reason: str,
        promoted_by: str,
        min_confidence: float = 0.85,
    ) -> MemoryBankRecord:
        node = self.doc_store.get_current(memory_id)
        if node is None:
            raise ValueError("memory_not_found")
        if node.confidence < min_confidence:
            raise ValueError("confidence_below_threshold")
        if not node.source:
            raise ValueError("source_required")

        edges = self.graph_store.edges_for_node(memory_id)
        for edge in edges:
            if edge.relation_type == "contradicts" and edge.weight >= 0.6:
                raise ValueError("contradiction_detected")

        record = MemoryBankRecord(
            origin_memory_id=node.memory_id,
            tenant_id=node.tenant_id,
            user_id=node.user_id,
            memory_type=node.memory_type,
            text=node.text,
            payload=node.payload,
            confidence=node.confidence,
            importance=node.importance,
            promotion_reason=reason,
            promoted_by=promoted_by,
            source=node.source,
        )
        return self.bank_store.upsert_bank_record(record)

    def query_bank(self, *, user_id: str, query: str, top_k: int = 20) -> list[MemoryBankRecord]:
        return self.bank_store.query_bank(user_id=user_id, query=query, top_k=top_k)

    def approve(self, *, bank_id: str, reviewer: str) -> MemoryBankRecord | None:
        return self.bank_store.review_bank_record(bank_id, status="approved", reviewer=reviewer)

    def reject(self, *, bank_id: str, reviewer: str) -> MemoryBankRecord | None:
        return self.bank_store.review_bank_record(bank_id, status="rejected", reviewer=reviewer)
