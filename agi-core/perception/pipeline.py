from __future__ import annotations

import re
from typing import Any

from runtime.models import Observation
from runtime.energy import EnergyAllocator
from runtime.models import utc_now


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "have", "will",
    "then", "when", "what", "where", "which", "about", "must", "should", "could", "would",
}


class PerceptionPipeline:
    def __init__(self) -> None:
        self.energy = EnergyAllocator()

    def perceive(
        self,
        *,
        cycle_id: int,
        raw_input: str,
        environment: dict[str, Any] | None = None,
    ) -> Observation:
        text = (raw_input or "").strip()
        entities = self.extract_entities(text)
        events = self.detect_events(text)
        goals = self.detect_goals(text)
        relationships = self.map_relationships(entities)
        state = self.build_state(text=text, environment=environment or {}, entities=entities, events=events)
        importance = self.energy.score(
            relevance=min(1.0, 0.2 + (0.08 * len(entities)) + (0.1 * len(goals))),
            urgency=0.95 if any("immediate" in item.lower() or "now" in item.lower() for item in goals + events) else 0.65,
            reward=0.9 if goals else 0.55,
        ).importance
        return Observation(
            cycle_id=cycle_id,
            timestamp_utc=utc_now(),
            raw_input=text,
            entities=entities,
            events=events,
            inferred_goals=goals,
            state=state,
            relationships=relationships,
            importance=importance,
        )

    def extract_entities(self, text: str) -> list[str]:
        candidates = re.findall(r"\b[A-Z][A-Za-z0-9_.:-]+\b", text)
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b", text)
        out: list[str] = []
        for item in candidates + tokens:
            lowered = item.lower()
            if lowered in _STOPWORDS:
                continue
            if item not in out:
                out.append(item)
        return out[:20]

    def detect_events(self, text: str) -> list[str]:
        event_markers = {
            "build": "build_requested",
            "deploy": "deploy_requested",
            "verify": "verification_requested",
            "learn": "learning_requested",
            "scale": "scaling_requested",
            "remember": "memory_update_requested",
            "report": "report_requested",
        }
        events = [value for key, value in event_markers.items() if key in text.lower()]
        return events or ["state_observed"]

    def detect_goals(self, text: str) -> list[str]:
        patterns = [
            r"goal:\s*([^.;\n]+)",
            r"build\s+([^.;\n]+)",
            r"create\s+([^.;\n]+)",
            r"implement\s+([^.;\n]+)",
            r"verify\s+([^.;\n]+)",
        ]
        out: list[str] = []
        for pattern in patterns:
            for match in re.findall(pattern, text, flags=re.IGNORECASE):
                cleaned = " ".join(match.split()).strip()
                if cleaned and cleaned not in out:
                    out.append(cleaned)
        return out[:10]

    def map_relationships(self, entities: list[str]) -> list[dict[str, Any]]:
        relationships = []
        for left, right in zip(entities, entities[1:]):
            relationships.append({"from": left, "to": right, "relation": "associated_with"})
        return relationships[:20]

    def build_state(
        self,
        *,
        text: str,
        environment: dict[str, Any],
        entities: list[str],
        events: list[str],
    ) -> dict[str, Any]:
        return {
            "text_length": len(text),
            "entity_count": len(entities),
            "event_count": len(events),
            "environment": environment,
            "has_deadline": "deadline" in text.lower() or "t-minus" in text.lower(),
        }
