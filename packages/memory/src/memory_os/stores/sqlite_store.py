from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..embeddings import cosine_similarity, deterministic_hash_embedding
from ..memory_types import MemoryBankRecord, MemoryEdge, MemoryNode, Reminder, utc_now
from .interfaces import DocStore, EventStore, GraphStore, MemoryBankStore, ReminderStore, VectorStore


def _dt_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _iso_to_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


class SQLiteMemoryStore(DocStore, VectorStore, GraphStore, EventStore, ReminderStore, MemoryBankStore):
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._bootstrap()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _bootstrap(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS memory_nodes (
                    row_id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    event_time TEXT,
                    text TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    embedding_json TEXT,
                    tags_json TEXT NOT NULL,
                    entities_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    importance REAL NOT NULL,
                    source_json TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    supersedes TEXT,
                    privacy TEXT NOT NULL,
                    policy_json TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    channel_id TEXT,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed_at TEXT,
                    is_current INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(memory_id, version)
                );
                CREATE INDEX IF NOT EXISTS idx_memory_current ON memory_nodes(memory_id, is_current);
                CREATE INDEX IF NOT EXISTS idx_memory_user_type ON memory_nodes(user_id, memory_type, is_current);
                CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory_nodes(user_id, tier, is_current);

                CREATE TABLE IF NOT EXISTS memory_edges (
                    edge_id TEXT PRIMARY KEY,
                    src_id TEXT NOT NULL,
                    dst_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    evidence_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_edges_src ON memory_edges(src_id);
                CREATE INDEX IF NOT EXISTS idx_edges_dst ON memory_edges(dst_id);

                CREATE TABLE IF NOT EXISTS reminders (
                    reminder_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    due_at TEXT,
                    cron TEXT,
                    condition_expr TEXT,
                    trigger_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    linked_goal_id TEXT,
                    linked_memory_id TEXT,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_fired_at TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(user_id, status, due_at);

                CREATE TABLE IF NOT EXISTS memory_bank (
                    bank_id TEXT PRIMARY KEY,
                    origin_memory_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    importance REAL NOT NULL,
                    promotion_reason TEXT NOT NULL,
                    promoted_by TEXT NOT NULL,
                    promoted_at TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    source_json TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    embedding_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_bank_user ON memory_bank(user_id, review_status);

                CREATE TABLE IF NOT EXISTS l2_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> MemoryNode:
        return MemoryNode(
            memory_id=row["memory_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            agent_id=row["agent_id"],
            memory_type=row["memory_type"],
            created_at=_iso_to_dt(row["created_at"]) or utc_now(),
            updated_at=_iso_to_dt(row["updated_at"]) or utc_now(),
            event_time=_iso_to_dt(row["event_time"]),
            text=row["text"],
            payload=json.loads(row["payload_json"] or "{}"),
            embedding=json.loads(row["embedding_json"]) if row["embedding_json"] else None,
            tags=json.loads(row["tags_json"] or "[]"),
            entities=json.loads(row["entities_json"] or "[]"),
            confidence=float(row["confidence"]),
            importance=float(row["importance"]),
            source=json.loads(row["source_json"] or "{}"),
            version=int(row["version"]),
            supersedes=row["supersedes"],
            privacy=row["privacy"],
            policy=json.loads(row["policy_json"] or "{}"),
            tier=row["tier"],
            channel_id=row["channel_id"],
            access_count=int(row["access_count"] or 0),
            last_accessed_at=_iso_to_dt(row["last_accessed_at"]),
        )

    @staticmethod
    def _row_to_edge(row: sqlite3.Row) -> MemoryEdge:
        return MemoryEdge(
            edge_id=row["edge_id"],
            src_id=row["src_id"],
            dst_id=row["dst_id"],
            relation_type=row["relation_type"],
            weight=float(row["weight"]),
            created_at=_iso_to_dt(row["created_at"]) or utc_now(),
            evidence=json.loads(row["evidence_json"] or "{}"),
        )

    @staticmethod
    def _row_to_reminder(row: sqlite3.Row) -> Reminder:
        return Reminder(
            reminder_id=row["reminder_id"],
            user_id=row["user_id"],
            agent_id=row["agent_id"],
            title=row["title"],
            description=row["description"],
            due_at=_iso_to_dt(row["due_at"]),
            cron=row["cron"],
            condition=row["condition_expr"],
            trigger_type=row["trigger_type"],
            status=row["status"],
            linked_goal_id=row["linked_goal_id"],
            linked_memory_id=row["linked_memory_id"],
            priority=row["priority"],
            created_at=_iso_to_dt(row["created_at"]) or utc_now(),
            last_fired_at=_iso_to_dt(row["last_fired_at"]),
            payload=json.loads(row["payload_json"] or "{}"),
        )

    @staticmethod
    def _row_to_bank(row: sqlite3.Row) -> MemoryBankRecord:
        return MemoryBankRecord(
            bank_id=row["bank_id"],
            origin_memory_id=row["origin_memory_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            memory_type=row["memory_type"],
            text=row["text"],
            payload=json.loads(row["payload_json"] or "{}"),
            confidence=float(row["confidence"]),
            importance=float(row["importance"]),
            promotion_reason=row["promotion_reason"],
            promoted_by=row["promoted_by"],
            promoted_at=_iso_to_dt(row["promoted_at"]) or utc_now(),
            review_status=row["review_status"],
            approved_by=row["approved_by"],
            approved_at=_iso_to_dt(row["approved_at"]),
            source=json.loads(row["source_json"] or "{}"),
            version=int(row["version"]),
        )

    def write_node(self, node: MemoryNode, expected_version: int | None = None) -> MemoryNode:
        now = utc_now()
        with self._lock, self._connect() as conn:
            current = conn.execute(
                "SELECT * FROM memory_nodes WHERE memory_id = ? AND is_current = 1",
                (node.memory_id,),
            ).fetchone()

            if current is not None:
                current_version = int(current["version"])
                if expected_version is not None and expected_version != current_version:
                    raise ValueError("version_conflict")
                new_version = current_version + 1
                supersedes = current["row_id"]
                conn.execute("UPDATE memory_nodes SET is_current = 0 WHERE row_id = ?", (current["row_id"],))
            else:
                if expected_version not in (None, 0):
                    raise ValueError("version_conflict")
                new_version = 1
                supersedes = node.supersedes

            row_id = f"{node.memory_id}:v{new_version}"
            embedding = node.embedding or deterministic_hash_embedding(node.text)
            written = node.model_copy(
                update={
                    "created_at": node.created_at if current is None else _iso_to_dt(current["created_at"]) or node.created_at,
                    "updated_at": now,
                    "embedding": embedding,
                    "version": new_version,
                    "supersedes": supersedes,
                }
            )

            conn.execute(
                """
                INSERT INTO memory_nodes (
                    row_id, memory_id, tenant_id, user_id, agent_id, memory_type,
                    created_at, updated_at, event_time, text, payload_json, embedding_json,
                    tags_json, entities_json, confidence, importance, source_json,
                    version, supersedes, privacy, policy_json, tier, channel_id,
                    access_count, last_accessed_at, is_current
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    row_id,
                    written.memory_id,
                    written.tenant_id,
                    written.user_id,
                    written.agent_id,
                    written.memory_type,
                    _dt_to_iso(written.created_at),
                    _dt_to_iso(written.updated_at),
                    _dt_to_iso(written.event_time),
                    written.text,
                    json.dumps(written.payload, sort_keys=True),
                    json.dumps(written.embedding),
                    json.dumps(written.tags),
                    json.dumps(written.entities),
                    float(written.confidence),
                    float(written.importance),
                    json.dumps(written.source, sort_keys=True),
                    int(written.version),
                    written.supersedes,
                    written.privacy,
                    json.dumps(written.policy, sort_keys=True),
                    written.tier,
                    written.channel_id,
                    int(written.access_count),
                    _dt_to_iso(written.last_accessed_at),
                ),
            )
            return written

    def get_current(self, memory_id: str) -> MemoryNode | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM memory_nodes WHERE memory_id = ? AND is_current = 1",
                (memory_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_node(row)

    def get_many(self, memory_ids: list[str]) -> list[MemoryNode]:
        if not memory_ids:
            return []
        placeholders = ",".join("?" for _ in memory_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM memory_nodes WHERE memory_id IN ({placeholders}) AND is_current = 1",
                tuple(memory_ids),
            ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def query_nodes(
        self,
        *,
        user_id: str,
        memory_types: list[str] | None = None,
        tier: str | None = None,
        include_archived: bool = False,
    ) -> list[MemoryNode]:
        clauses = ["is_current = 1", "user_id = ?"]
        params: list[object] = [user_id]
        if memory_types:
            placeholders = ",".join("?" for _ in memory_types)
            clauses.append(f"memory_type IN ({placeholders})")
            params.extend(memory_types)
        if tier:
            clauses.append("tier = ?")
            params.append(tier)
        if not include_archived:
            clauses.append("tier != 'archive'")

        query = "SELECT * FROM memory_nodes WHERE " + " AND ".join(clauses) + " ORDER BY updated_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._row_to_node(row) for row in rows]

    def semantic_search(
        self,
        *,
        query_embedding: list[float],
        user_id: str,
        memory_types: list[str] | None = None,
        top_k: int = 20,
        tier: str | None = None,
    ) -> list[tuple[MemoryNode, float]]:
        candidates = self.query_nodes(user_id=user_id, memory_types=memory_types, tier=tier)
        ranked: list[tuple[MemoryNode, float]] = []
        for node in candidates:
            if not node.embedding:
                continue
            score = cosine_similarity(query_embedding, node.embedding)
            ranked.append((node, float(score)))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[: max(1, int(top_k))]

    def update_access(self, memory_ids: list[str], accessed_at: datetime) -> None:
        if not memory_ids:
            return
        with self._lock, self._connect() as conn:
            for memory_id in memory_ids:
                conn.execute(
                    """
                    UPDATE memory_nodes
                    SET access_count = access_count + 1, last_accessed_at = ?
                    WHERE memory_id = ? AND is_current = 1
                    """,
                    (_dt_to_iso(accessed_at), memory_id),
                )

    def set_tier(self, memory_ids: list[str], tier: str) -> None:
        if not memory_ids:
            return
        with self._lock, self._connect() as conn:
            for memory_id in memory_ids:
                conn.execute(
                    "UPDATE memory_nodes SET tier = ? WHERE memory_id = ? AND is_current = 1",
                    (tier, memory_id),
                )

    def count_by_tier(self, user_id: str) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT tier, COUNT(*) AS count FROM memory_nodes WHERE user_id = ? AND is_current = 1 GROUP BY tier",
                (user_id,),
            ).fetchall()
        return {str(row["tier"]): int(row["count"]) for row in rows}

    def write_edge(self, edge: MemoryEdge) -> MemoryEdge:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_edges (
                    edge_id, src_id, dst_id, relation_type, weight, created_at, evidence_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge.edge_id,
                    edge.src_id,
                    edge.dst_id,
                    edge.relation_type,
                    float(edge.weight),
                    _dt_to_iso(edge.created_at),
                    json.dumps(edge.evidence, sort_keys=True),
                ),
            )
        return edge

    def edges_for_node(self, memory_id: str) -> list[MemoryEdge]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_edges WHERE src_id = ? OR dst_id = ? ORDER BY created_at DESC",
                (memory_id, memory_id),
            ).fetchall()
        return [self._row_to_edge(row) for row in rows]

    def list_since(self, *, user_id: str, since: datetime, limit: int = 200) -> list[MemoryNode]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM memory_nodes
                WHERE user_id = ? AND is_current = 1 AND updated_at >= ?
                ORDER BY updated_at ASC
                LIMIT ?
                """,
                (user_id, _dt_to_iso(since), int(limit)),
            ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def create_reminder(self, reminder: Reminder) -> Reminder:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO reminders (
                    reminder_id, user_id, agent_id, title, description, due_at, cron,
                    condition_expr, trigger_type, status, linked_goal_id, linked_memory_id,
                    priority, created_at, last_fired_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reminder.reminder_id,
                    reminder.user_id,
                    reminder.agent_id,
                    reminder.title,
                    reminder.description,
                    _dt_to_iso(reminder.due_at),
                    reminder.cron,
                    reminder.condition,
                    reminder.trigger_type,
                    reminder.status,
                    reminder.linked_goal_id,
                    reminder.linked_memory_id,
                    reminder.priority,
                    _dt_to_iso(reminder.created_at),
                    _dt_to_iso(reminder.last_fired_at),
                    json.dumps(reminder.payload, sort_keys=True),
                ),
            )
        return reminder

    def due_reminders(self, *, now: datetime, user_id: str, limit: int = 50) -> list[Reminder]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reminders
                WHERE user_id = ? AND status = 'scheduled' AND due_at IS NOT NULL AND due_at <= ?
                ORDER BY due_at ASC
                LIMIT ?
                """,
                (user_id, _dt_to_iso(now), int(limit)),
            ).fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def ack_reminder(self, reminder_id: str, *, status: str = "acked") -> Reminder | None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = ?, last_fired_at = ? WHERE reminder_id = ?",
                (status, _dt_to_iso(utc_now()), reminder_id),
            )
            row = conn.execute("SELECT * FROM reminders WHERE reminder_id = ?", (reminder_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_reminder(row)

    def mark_reminder_fired(self, reminder_id: str) -> Reminder | None:
        return self.ack_reminder(reminder_id, status="fired")

    def upsert_bank_record(self, record: MemoryBankRecord) -> MemoryBankRecord:
        embedding = deterministic_hash_embedding(record.text)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_bank (
                    bank_id, origin_memory_id, tenant_id, user_id, memory_type, text,
                    payload_json, confidence, importance, promotion_reason, promoted_by,
                    promoted_at, review_status, approved_by, approved_at, source_json,
                    version, embedding_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.bank_id,
                    record.origin_memory_id,
                    record.tenant_id,
                    record.user_id,
                    record.memory_type,
                    record.text,
                    json.dumps(record.payload, sort_keys=True),
                    float(record.confidence),
                    float(record.importance),
                    record.promotion_reason,
                    record.promoted_by,
                    _dt_to_iso(record.promoted_at),
                    record.review_status,
                    record.approved_by,
                    _dt_to_iso(record.approved_at),
                    json.dumps(record.source, sort_keys=True),
                    int(record.version),
                    json.dumps(embedding),
                ),
            )
        return record

    def query_bank(self, *, user_id: str, query: str, top_k: int = 20) -> list[MemoryBankRecord]:
        query_vec = deterministic_hash_embedding(query)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_bank WHERE user_id = ? ORDER BY promoted_at DESC",
                (user_id,),
            ).fetchall()
        scored: list[tuple[MemoryBankRecord, float]] = []
        for row in rows:
            record = self._row_to_bank(row)
            emb = json.loads(row["embedding_json"] or "[]")
            score = cosine_similarity(query_vec, emb)
            scored.append((record, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [item[0] for item in scored[: max(1, int(top_k))]]

    def review_bank_record(self, bank_id: str, *, status: str, reviewer: str) -> MemoryBankRecord | None:
        now = utc_now()
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE memory_bank SET review_status = ?, approved_by = ?, approved_at = ? WHERE bank_id = ?",
                (status, reviewer, _dt_to_iso(now), bank_id),
            )
            row = conn.execute("SELECT * FROM memory_bank WHERE bank_id = ?", (bank_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_bank(row)

    def get_cache(self, key: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload_json FROM l2_cache WHERE cache_key = ?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row["payload_json"])

    def set_cache(self, key: str, payload: dict) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO l2_cache (cache_key, payload_json, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(payload, sort_keys=True), _dt_to_iso(utc_now())),
            )

    def all_current_nodes(self, *, user_id: str) -> list[MemoryNode]:
        return self.query_nodes(user_id=user_id, include_archived=True)
