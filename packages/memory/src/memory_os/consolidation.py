from __future__ import annotations

import math
from datetime import datetime

from .budgets import compress_candidates
from .memory_types import MemoryNode, utc_now


class ConsolidationEngine:
    def relevance_decay(self, node: MemoryNode, *, now: datetime | None = None, lam: float = 0.02) -> float:
        now = now or utc_now()
        age_seconds = max(0.0, (now - node.updated_at).total_seconds())
        age_hours = age_seconds / 3600.0
        return float(node.importance) * math.exp(-lam * age_hours)

    def summarize_episode(self, node: MemoryNode) -> str:
        text = node.text.strip()
        if len(text) <= 160:
            return text
        return text[:157] + "..."

    def derive_semantic_candidates(self, node: MemoryNode) -> list[MemoryNode]:
        candidates: list[MemoryNode] = []
        facts = node.payload.get("facts", []) if isinstance(node.payload, dict) else []
        for fact in facts:
            fact_text = str(fact).strip()
            if not fact_text:
                continue
            candidates.append(
                MemoryNode(
                    tenant_id=node.tenant_id,
                    user_id=node.user_id,
                    agent_id=node.agent_id,
                    memory_type="semantic",
                    text=fact_text,
                    payload={"derived_from": node.memory_id},
                    tags=list(set(node.tags + ["consolidated", "semantic"])),
                    entities=node.entities,
                    confidence=min(1.0, node.confidence * 0.95),
                    importance=min(1.0, node.importance * 0.9),
                    source={**node.source, "consolidation": "episodic_to_semantic"},
                    privacy=node.privacy,
                    policy=node.policy,
                    tier="warm",
                    channel_id=node.channel_id,
                )
            )
        return candidates

    def derive_procedural_candidates(self, node: MemoryNode) -> list[MemoryNode]:
        tools = []
        if isinstance(node.payload, dict):
            tools = node.payload.get("tools", [])
        if not tools:
            return []
        text = " -> ".join(str(tool) for tool in tools)
        return [
            MemoryNode(
                tenant_id=node.tenant_id,
                user_id=node.user_id,
                agent_id=node.agent_id,
                memory_type="procedural",
                text=f"Workflow: {text}",
                payload={"derived_from": node.memory_id, "tools": list(tools)},
                tags=list(set(node.tags + ["consolidated", "procedural"])),
                entities=node.entities,
                confidence=min(1.0, node.confidence * 0.92),
                importance=min(1.0, node.importance * 0.93),
                source={**node.source, "consolidation": "episodic_to_procedural"},
                privacy=node.privacy,
                policy=node.policy,
                tier="warm",
                channel_id=node.channel_id,
            )
        ]

    def dedupe_pairs(self, nodes: list[MemoryNode]) -> list[tuple[MemoryNode, MemoryNode]]:
        return compress_candidates(nodes)
