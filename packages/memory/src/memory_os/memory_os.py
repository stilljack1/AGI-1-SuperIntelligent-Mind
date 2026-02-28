from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .budgets import BudgetConfig, enforce_budgets
from .caching import L1Cache
from .consolidation import ConsolidationEngine
from .embeddings import deterministic_hash_embedding
from .habits import HabitEngine
from .memory_bank import MemoryBankService
from .memory_types import ContextBundle, MemoryEdge, MemoryNode, Reminder, utc_now
from .permissions import MemoryAccessController
from .reminders import ReminderService
from .sharding import ShardManager
from .stores.sqlite_store import SQLiteMemoryStore
from .tiering import TierManager


@dataclass(frozen=True)
class MemoryOSConfig:
    db_path: str
    shard_count: int = 1
    l1_cache_capacity: int = 256
    budget_hot: int = 500
    budget_warm: int = 2000
    budget_cold: int = 5000
    cloud_enabled: bool = False
    cloud_ddb_table: str = ""
    cloud_s3_bucket: str = ""
    aws_region: str = "us-east-1"


class MemoryOS:
    def __init__(self, config: MemoryOSConfig) -> None:
        self.config = config
        self.shards = ShardManager(base_db_path=config.db_path, shard_count=config.shard_count)
        self.l1 = L1Cache(capacity=config.l1_cache_capacity)
        self.access = MemoryAccessController()
        self.tiering = TierManager()
        self.budget = BudgetConfig(
            max_nodes_hot=config.budget_hot,
            max_nodes_warm=config.budget_warm,
            max_nodes_cold=config.budget_cold,
        )
        self.consolidation = ConsolidationEngine()
        self.habits = HabitEngine()

        primary = self.shards.all_stores()[0]
        self.reminders = ReminderService(primary)
        self.bank = MemoryBankService(doc_store=primary, graph_store=primary, bank_store=primary)

        self._boto3 = None
        if config.cloud_enabled and config.cloud_ddb_table:
            try:
                import boto3  # type: ignore

                self._boto3 = boto3
            except Exception:
                self._boto3 = None

    @classmethod
    def from_env(cls, *, db_path: str) -> "MemoryOS":
        return cls(
            MemoryOSConfig(
                db_path=db_path,
                shard_count=int(os.getenv("AGI1_MEMORY_SHARDS", "1")),
                l1_cache_capacity=int(os.getenv("AGI1_MEMORY_L1_CAPACITY", "256")),
                budget_hot=int(os.getenv("AGI1_MEMORY_BUDGET_HOT", "500")),
                budget_warm=int(os.getenv("AGI1_MEMORY_BUDGET_WARM", "2000")),
                budget_cold=int(os.getenv("AGI1_MEMORY_BUDGET_COLD", "5000")),
                cloud_enabled=os.getenv("AGI1_MEMORY_CLOUD_ENABLED", "false").lower() in {"1", "true", "yes"},
                cloud_ddb_table=os.getenv("AGI1_MEMORY_DDB_TABLE", "").strip(),
                cloud_s3_bucket=os.getenv("AGI1_MEMORY_S3_BUCKET", "").strip(),
                aws_region=os.getenv("AWS_REGION", "us-east-1"),
            )
        )

    def _store_for(self, *, user_id: str, memory_type: str) -> SQLiteMemoryStore:
        return self.shards.store_for(user_id=user_id, memory_type=memory_type)

    def write_memory(
        self,
        *,
        tenant_id: str,
        user_id: str,
        agent_id: str,
        memory_type: str,
        text: str,
        payload: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        entities: list[str] | None = None,
        confidence: float = 0.6,
        importance: float = 0.6,
        source: dict[str, Any] | None = None,
        privacy: str = "private",
        policy: dict[str, Any] | None = None,
        memory_id: str | None = None,
        expected_version: int | None = None,
        event_time: datetime | None = None,
        tier: str | None = None,
        channel_id: str | None = None,
    ) -> MemoryNode:
        decision = self.access.can_write(
            target_user_id=user_id,
            request_user_id=user_id,
            request_agent_id=agent_id,
            privacy=privacy,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)

        node = MemoryNode(
            memory_id=memory_id or f"mem_{int(utc_now().timestamp() * 1000)}_{os.urandom(6).hex()}",
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=agent_id,
            memory_type=memory_type,
            event_time=event_time,
            text=text,
            payload=payload or {},
            tags=tags or [],
            entities=entities or [],
            confidence=confidence,
            importance=importance,
            source=source or {},
            privacy=privacy,
            policy=policy or {},
            tier=tier or ("hot" if memory_type in {"working", "prospective"} else "warm"),
            channel_id=channel_id,
        )

        store = self._store_for(user_id=user_id, memory_type=memory_type)
        written = store.write_node(node, expected_version=expected_version)
        self._write_cloud_audit(written)
        self._auto_link(written, store=store)
        self.l1.clear()
        return written

    def _write_cloud_audit(self, node: MemoryNode) -> None:
        if not self._boto3 or not self.config.cloud_ddb_table:
            return
        try:
            client = self._boto3.client("dynamodb", region_name=self.config.aws_region)
            client.put_item(
                TableName=self.config.cloud_ddb_table,
                Item={
                    "pk": {"S": f"mem#{node.user_id}"},
                    "sk": {"S": f"{node.memory_id}#{node.version}"},
                    "agent_id": {"S": node.agent_id},
                    "memory_type": {"S": node.memory_type},
                    "confidence": {"N": f"{node.confidence:.4f}"},
                    "importance": {"N": f"{node.importance:.4f}"},
                    "timestamp": {"S": node.updated_at.isoformat()},
                },
            )
        except Exception:
            return

    def _auto_link(self, node: MemoryNode, *, store: SQLiteMemoryStore) -> None:
        if node.memory_type == "episodic":
            sem_candidates = self.consolidation.derive_semantic_candidates(node)
            for sem in sem_candidates:
                written = store.write_node(sem)
                store.write_edge(
                    MemoryEdge(
                        src_id=node.memory_id,
                        dst_id=written.memory_id,
                        relation_type="derived_from",
                        weight=0.9,
                        evidence={"rule": "episodic_to_semantic"},
                    )
                )

            proc_candidates = self.consolidation.derive_procedural_candidates(node)
            for proc in proc_candidates:
                written = store.write_node(proc)
                store.write_edge(
                    MemoryEdge(
                        src_id=node.memory_id,
                        dst_id=written.memory_id,
                        relation_type="derived_from",
                        weight=0.86,
                        evidence={"rule": "episodic_to_procedural"},
                    )
                )

        if node.memory_type in {"semantic", "identity"}:
            similar = store.query_nodes(user_id=node.user_id, memory_types=[node.memory_type])
            for other in similar[:80]:
                if other.memory_id == node.memory_id:
                    continue
                if set(other.entities) & set(node.entities) and other.text.lower() != node.text.lower():
                    if " not " in node.text.lower() or " not " in other.text.lower():
                        store.write_edge(
                            MemoryEdge(
                                src_id=node.memory_id,
                                dst_id=other.memory_id,
                                relation_type="contradicts",
                                weight=max(node.confidence, other.confidence),
                                evidence={"rule": "entity_conflict"},
                            )
                        )

        if node.memory_type == "prospective":
            store.write_edge(
                MemoryEdge(
                    src_id=node.memory_id,
                    dst_id=node.memory_id,
                    relation_type="reminder_of",
                    weight=1.0,
                    evidence={"rule": "prospective_self_link"},
                )
            )

    def link_memory(
        self,
        *,
        user_id: str,
        src_id: str,
        dst_id: str,
        relation_type: str,
        weight: float,
        evidence: dict[str, Any] | None = None,
    ) -> MemoryEdge:
        store = self._store_for(user_id=user_id, memory_type="semantic")
        edge = MemoryEdge(
            src_id=src_id,
            dst_id=dst_id,
            relation_type=relation_type,
            weight=weight,
            evidence=evidence or {},
        )
        return store.write_edge(edge)

    def query_memory(
        self,
        *,
        user_id: str,
        agent_id: str,
        query: str,
        memory_types: list[str] | None = None,
        top_k: int = 20,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        memory_types = memory_types or []
        cache_key = json.dumps(
            {
                "u": user_id,
                "a": agent_id,
                "q": query,
                "t": sorted(memory_types),
                "k": top_k,
                "arch": include_archived,
            },
            sort_keys=True,
        )

        cached = self.l1.get(cache_key)
        store = self._store_for(user_id=user_id, memory_type="semantic")
        if cached is None:
            cached = store.get_cache(cache_key)
            if cached is not None:
                self.l1.set(cache_key, cached)
        if cached is not None:
            return cached

        query_embedding = deterministic_hash_embedding(query)
        ranked: dict[str, tuple[MemoryNode, float]] = {}
        tiers = ["hot", "warm", "cold"] + (["archive"] if include_archived else [])
        for tier in tiers:
            results = store.semantic_search(
                query_embedding=query_embedding,
                user_id=user_id,
                memory_types=memory_types or None,
                top_k=max(top_k, 20),
                tier=tier,
            )
            for node, score in results:
                current = ranked.get(node.memory_id)
                if current is None or score > current[1]:
                    ranked[node.memory_id] = (node, score)

        items = sorted(ranked.values(), key=lambda row: row[1], reverse=True)
        filtered = []
        for node, score in items:
            decision = self.access.can_read(node, request_user_id=user_id, request_agent_id=agent_id)
            if decision.allowed:
                filtered.append((node, score))

        filtered = filtered[: max(1, int(top_k))]
        now = utc_now()
        store.update_access([node.memory_id for node, _ in filtered], accessed_at=now)
        payload = {
            "query": query,
            "count": len(filtered),
            "results": [
                {
                    "memory": node.model_dump(mode="json"),
                    "score": round(float(score), 6),
                }
                for node, score in filtered
            ],
            "cache": {
                "l1": self.l1.stats().__dict__,
                "used": False,
            },
        }
        self.l1.set(cache_key, payload)
        store.set_cache(cache_key, payload)
        return payload

    def build_context(
        self,
        *,
        user_id: str,
        agent_id: str,
        query: str,
        task_state: dict[str, Any] | None = None,
    ) -> ContextBundle:
        store = self._store_for(user_id=user_id, memory_type="semantic")
        now = utc_now()

        working = self.access.filter_readable(
            store.query_nodes(user_id=user_id, memory_types=["working"])[:15],
            request_user_id=user_id,
            request_agent_id=agent_id,
        )
        episodic = self.access.filter_readable(
            store.query_nodes(user_id=user_id, memory_types=["episodic"])[:20],
            request_user_id=user_id,
            request_agent_id=agent_id,
        )
        semantic = [item[0] for item in store.semantic_search(
            query_embedding=deterministic_hash_embedding(query),
            user_id=user_id,
            memory_types=["semantic"],
            top_k=15,
        )]
        procedural = [item[0] for item in store.semantic_search(
            query_embedding=deterministic_hash_embedding(query),
            user_id=user_id,
            memory_types=["procedural"],
            top_k=10,
        )]
        identity = self.access.filter_readable(
            store.query_nodes(user_id=user_id, memory_types=["identity"])[:10],
            request_user_id=user_id,
            request_agent_id=agent_id,
        )
        due = self.reminders.get_due_reminders(user_id=user_id, now=now, limit=10)

        contradictions: list[MemoryEdge] = []
        for node in semantic[:8]:
            contradictions.extend(
                edge for edge in store.edges_for_node(node.memory_id) if edge.relation_type == "contradicts"
            )

        confidence_gaps: list[str] = []
        for node in semantic[:15] + procedural[:10]:
            if node.confidence < 0.5:
                confidence_gaps.append(f"low_confidence:{node.memory_id}")

        bundle = ContextBundle(
            user_id=user_id,
            agent_id=agent_id,
            query=query,
            working=working,
            episodic=episodic,
            semantic=semantic,
            procedural=procedural,
            identity=identity,
            reminders=due,
            contradictions=contradictions[:20],
            confidence_gaps=confidence_gaps[:20],
        )

        if task_state:
            wm = MemoryNode(
                tenant_id="FairGroup",
                user_id=user_id,
                agent_id=agent_id,
                memory_type="working",
                text=f"Task state snapshot for {task_state.get('task_id', 'unknown')}",
                payload={"task_state": task_state},
                confidence=0.8,
                importance=0.85,
                source={"source": "context_builder"},
                privacy="shared",
                policy={"allowed_agents": [agent_id, "singularity", "aegis"]},
                tier="hot",
            )
            store.write_node(wm)
            bundle.working.insert(0, wm)

        return bundle

    def consolidate(self, *, user_id: str, agent_id: str) -> dict[str, Any]:
        store = self._store_for(user_id=user_id, memory_type="episodic")
        nodes = store.query_nodes(user_id=user_id, include_archived=True)

        converted = {"working_to_episodic": 0, "episodic_to_semantic": 0, "episodic_to_procedural": 0}

        for node in nodes:
            if node.memory_type == "working":
                episodic = MemoryNode(
                    tenant_id=node.tenant_id,
                    user_id=node.user_id,
                    agent_id=agent_id,
                    memory_type="episodic",
                    text=self.consolidation.summarize_episode(node),
                    payload={**node.payload, "from_working": node.memory_id},
                    tags=list(set(node.tags + ["consolidated"])),
                    entities=node.entities,
                    confidence=min(1.0, node.confidence * 0.95),
                    importance=min(1.0, node.importance * 0.9),
                    source={**node.source, "consolidation": "working_to_episodic"},
                    privacy=node.privacy,
                    policy=node.policy,
                    tier="warm",
                    channel_id=node.channel_id,
                )
                store.write_node(episodic)
                converted["working_to_episodic"] += 1

            if node.memory_type == "episodic":
                sem = self.consolidation.derive_semantic_candidates(node)
                for item in sem:
                    store.write_node(item)
                    converted["episodic_to_semantic"] += 1

                proc = self.consolidation.derive_procedural_candidates(node)
                for item in proc:
                    store.write_node(item)
                    converted["episodic_to_procedural"] += 1

        self.run_tiering(user_id=user_id)
        self.l1.clear()

        refreshed = store.query_nodes(user_id=user_id, memory_types=["episodic"])
        habits = self.habits.detect_habits(refreshed)

        return {
            "status": "ok",
            "converted": converted,
            "habits_proposed": habits,
            "tier_counts": store.count_by_tier(user_id),
        }

    def run_tiering(self, *, user_id: str) -> dict[str, Any]:
        store = self._store_for(user_id=user_id, memory_type="semantic")
        nodes = store.all_current_nodes(user_id=user_id)
        migration = self.tiering.migrate_plan(nodes)
        for tier, memory_ids in migration.items():
            store.set_tier(memory_ids, tier)

        refreshed = store.all_current_nodes(user_id=user_id)
        nodes_by_tier: dict[str, list[MemoryNode]] = {"hot": [], "warm": [], "cold": [], "archive": []}
        for node in refreshed:
            nodes_by_tier.setdefault(node.tier, []).append(node)

        budget_actions = enforce_budgets(nodes_by_tier, self.budget)
        for action in budget_actions.values():
            if action:
                store.set_tier([node.memory_id for node in action], "archive")

        return {
            "migration": {key: len(value) for key, value in migration.items()},
            "budget_actions": {key: len(value) for key, value in budget_actions.items()},
            "tier_counts": store.count_by_tier(user_id),
        }

    def create_reminder(self, reminder: Reminder) -> Reminder:
        return self.reminders.create_reminder(reminder)

    def due_reminders_with_plan(self, *, user_id: str, agent_id: str, limit: int = 20) -> list[dict[str, Any]]:
        due = self.reminders.get_due_reminders(user_id=user_id, limit=limit)
        store = self._store_for(user_id=user_id, memory_type="working")
        output: list[dict[str, Any]] = []
        for reminder in due:
            task_stub = {
                "title": reminder.title,
                "steps": [
                    "Review reminder context",
                    "Draft execution plan",
                    "Request confirmation if external side effects",
                ],
                "linked_goal_id": reminder.linked_goal_id,
                "priority": reminder.priority,
            }
            working = MemoryNode(
                tenant_id="FairGroup",
                user_id=user_id,
                agent_id=agent_id,
                memory_type="working",
                text=f"Reminder fired: {reminder.title}",
                payload={"reminder_id": reminder.reminder_id, "task_plan_stub": task_stub},
                tags=["reminder", "working"],
                confidence=0.95,
                importance=0.9,
                source={"source": "reminder_trigger", "reminder_id": reminder.reminder_id},
                privacy="shared",
                policy={"allowed_agents": [agent_id, "singularity", "aegis"]},
                tier="hot",
            )
            stored = store.write_node(working)
            store.write_edge(
                MemoryEdge(
                    src_id=reminder.linked_memory_id or stored.memory_id,
                    dst_id=stored.memory_id,
                    relation_type="reminder_of",
                    weight=1.0,
                    evidence={"reminder_id": reminder.reminder_id},
                )
            )
            output.append({"reminder": reminder.model_dump(mode="json"), "task_plan_stub": task_stub, "working_memory": stored.model_dump(mode="json")})
        return output

    def ack_reminder(self, reminder_id: str) -> Reminder | None:
        return self.reminders.ack_reminder(reminder_id)

    def promote_to_bank(
        self,
        *,
        memory_id: str,
        reason: str,
        promoted_by: str,
        min_confidence: float = 0.85,
    ):
        return self.bank.promote_to_bank(
            memory_id=memory_id,
            reason=reason,
            promoted_by=promoted_by,
            min_confidence=min_confidence,
        )

    def query_bank(self, *, user_id: str, query: str, top_k: int = 20):
        return self.bank.query_bank(user_id=user_id, query=query, top_k=top_k)

    def review_bank(self, *, bank_id: str, reviewer: str, approved: bool):
        if approved:
            return self.bank.approve(bank_id=bank_id, reviewer=reviewer)
        return self.bank.reject(bank_id=bank_id, reviewer=reviewer)

    def record_task_execution(
        self,
        *,
        user_id: str,
        agent_id: str,
        task_text: str,
        outcome: dict[str, Any],
        tools: list[str] | None = None,
    ) -> dict[str, Any]:
        episodic = self.write_memory(
            tenant_id="FairGroup",
            user_id=user_id,
            agent_id=agent_id,
            memory_type="episodic",
            text=task_text,
            payload={"outcome": outcome, "tools": tools or []},
            tags=["task_execution"],
            entities=[agent_id],
            confidence=0.82,
            importance=0.78,
            source={"source": "task_runtime"},
            privacy="shared",
            policy={"allowed_agents": ["jack", "julia", "singularity", "aegis"]},
        )
        return {"episodic_memory_id": episodic.memory_id, "version": episodic.version}

    def scaling_report(self, *, user_id: str) -> dict[str, Any]:
        store = self._store_for(user_id=user_id, memory_type="semantic")
        tier_counts = store.count_by_tier(user_id)
        return {
            "user_id": user_id,
            "tier_counts": tier_counts,
            "shards": [descriptor.__dict__ for descriptor in self.shards.descriptors()],
            "cache": self.l1.stats().__dict__,
        }
