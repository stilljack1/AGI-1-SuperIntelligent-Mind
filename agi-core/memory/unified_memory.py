from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from runtime.models import ExecutionResult, FeedbackRecord, GoalRecord, Observation


class UnifiedMemory:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.paths = {
            "working": self.root / "working_memory.json",
            "episodic": self.root / "episodic_memory.json",
            "semantic": self.root / "semantic_memory.json",
            "skill": self.root / "skill_memory.json",
            "causal": self.root / "causal_memory.json",
            "goals": self.root / "goal_memory.json",
        }
        self.state = {name: self._load(path) for name, path in self.paths.items()}

    def ingest_observation(self, observation: Observation) -> None:
        self.state["working"] = [
            {"type": "observation", "payload": observation.to_dict(), "importance": observation.importance}
        ] + [item for item in self.state["working"][:24]]
        self.state["episodic"].append({"type": "observation", "payload": observation.to_dict(), "importance": observation.importance})
        for entity in observation.entities:
            self._upsert_semantic(entity, source="perception")
        for event in observation.events:
            self._upsert_causal(trigger=event, outcome="observation_recorded", confidence=0.55)
        for goal in observation.inferred_goals:
            self.remember_goal(goal=goal, priority=observation.importance, urgency=0.8, reward=0.9, source="perception")
        self.persist()

    def remember_goal(self, *, goal: str, priority: float, urgency: float, reward: float, source: str) -> GoalRecord:
        record = GoalRecord(
            goal_id=f"goal_{len(self.state['goals']) + 1:04d}",
            description=goal,
            priority=round(max(0.0, min(1.0, priority)), 6),
            urgency=round(max(0.0, min(1.0, urgency)), 6),
            reward=round(max(0.0, min(1.0, reward)), 6),
            source=source,
        )
        self.state["goals"] = [record.to_dict()] + [item for item in self.state["goals"] if item.get("description") != goal]
        self.persist()
        return record

    def remember_execution(self, result: ExecutionResult) -> None:
        payload = result.to_dict()
        self.state["episodic"].append({"type": "execution", "payload": payload, "importance": 0.8 if result.success else 0.95})
        self.state["skill"].append({"type": "execution_pattern", "payload": payload, "importance": 0.7})
        self.persist()

    def remember_feedback(self, feedback: FeedbackRecord) -> None:
        payload = feedback.to_dict()
        self.state["episodic"].append({"type": "feedback", "payload": payload, "importance": abs(feedback.reward)})
        if feedback.success:
            self._upsert_causal(trigger="executed_action", outcome="success", confidence=0.8)
        else:
            self._upsert_causal(trigger="executed_action", outcome="failure", confidence=0.9)
        self.persist()

    def remember_belief(self, belief: dict[str, Any]) -> None:
        self.state["semantic"].append(
            {
                "concept": str(belief.get("proposition", "belief")),
                "sources": ["belief_system"],
                "importance": float(belief.get("confidence", 0.5)),
            }
        )
        self.persist()

    def retrieve(self, query: str, *, top_k: int = 8) -> dict[str, list[dict[str, Any]]]:
        scored: dict[str, list[tuple[float, dict[str, Any]]]] = {}
        for name, records in self.state.items():
            ranked: list[tuple[float, dict[str, Any]]] = []
            for record in records:
                text = json.dumps(record, sort_keys=True).lower()
                score = self._similarity(query.lower(), text) + float(record.get("importance", 0.1))
                if score > 0:
                    ranked.append((score, record))
            ranked.sort(key=lambda row: row[0], reverse=True)
            scored[name] = ranked[:top_k]
        return {name: [item for _, item in items] for name, items in scored.items()}

    def consolidate(self) -> dict[str, Any]:
        working = self.state["working"][:25]
        episodic = sorted(self.state["episodic"], key=lambda item: float(item.get("importance", 0.0)), reverse=True)[:200]
        self.state["working"] = working
        self.state["episodic"] = episodic
        self.state["semantic"] = self._dedupe(self.state["semantic"], key="concept")
        self.state["skill"] = self._dedupe(self.state["skill"], key="type")
        self.state["causal"] = self._dedupe(self.state["causal"], key="key")
        self.state["goals"] = [goal for goal in self.state["goals"] if goal.get("status", "active") != "archived"][:100]
        self.persist()
        return {
            "working": len(self.state["working"]),
            "episodic": len(self.state["episodic"]),
            "semantic": len(self.state["semantic"]),
            "skill": len(self.state["skill"]),
            "causal": len(self.state["causal"]),
            "goals": len(self.state["goals"]),
        }

    def experience_replay(self, *, limit: int = 10) -> list[dict[str, Any]]:
        ranked = sorted(self.state["episodic"], key=lambda item: float(item.get("importance", 0.0)), reverse=True)
        return ranked[:limit]

    def active_goals(self, *, limit: int = 10) -> list[dict[str, Any]]:
        goals = [goal for goal in self.state["goals"] if goal.get("status", "active") == "active"]
        goals.sort(key=lambda item: (item.get("priority", 0.0), item.get("urgency", 0.0), item.get("reward", 0.0)), reverse=True)
        return goals[:limit]

    def summary(self) -> dict[str, Any]:
        return {name: len(records) for name, records in self.state.items()}

    def persist(self) -> None:
        for name, path in self.paths.items():
            path.write_text(json.dumps(self.state[name], indent=2), encoding="utf-8")

    def _upsert_semantic(self, concept: str, *, source: str) -> None:
        existing = {item["concept"]: item for item in self.state["semantic"] if "concept" in item}
        record = existing.get(concept, {"concept": concept, "sources": [], "importance": 0.4})
        if source not in record["sources"]:
            record["sources"].append(source)
        record["importance"] = round(min(1.0, float(record["importance"]) + 0.05), 6)
        existing[concept] = record
        self.state["semantic"] = list(existing.values())

    def _upsert_causal(self, *, trigger: str, outcome: str, confidence: float) -> None:
        key = f"{trigger}->{outcome}"
        existing = {item["key"]: item for item in self.state["causal"] if "key" in item}
        record = existing.get(key, {"key": key, "trigger": trigger, "outcome": outcome, "confidence": confidence, "importance": 0.6})
        record["confidence"] = round(max(float(record["confidence"]), confidence), 6)
        record["importance"] = round(min(1.0, float(record["importance"]) + 0.05), 6)
        existing[key] = record
        self.state["causal"] = list(existing.values())

    def _load(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def _dedupe(self, records: list[dict[str, Any]], *, key: str) -> list[dict[str, Any]]:
        seen: dict[str, dict[str, Any]] = {}
        for record in records:
            identifier = str(record.get(key) or json.dumps(record, sort_keys=True))
            current = seen.get(identifier)
            if current is None or float(record.get("importance", 0.0)) > float(current.get("importance", 0.0)):
                seen[identifier] = record
        return list(seen.values())

    def _similarity(self, query: str, text: str) -> float:
        q_tokens = {token for token in query.split() if token}
        t_tokens = {token for token in text.split() if token}
        if not q_tokens or not t_tokens:
            return 0.0
        overlap = len(q_tokens & t_tokens)
        if overlap == 0:
            return 0.0
        return overlap / math.sqrt(len(q_tokens) * len(t_tokens))
