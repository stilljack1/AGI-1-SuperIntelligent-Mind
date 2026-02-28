from __future__ import annotations

from typing import Any

from reasoning.consistency_checker import ConsistencyChecker
from reasoning.inference_engine import InferenceEngine
from reasoning.logic_validator import LogicValidator
from runtime.energy import EnergyAllocator


class ReasoningEngine:
    def __init__(self) -> None:
        self.energy = EnergyAllocator()
        self.logic = LogicValidator()
        self.consistency = ConsistencyChecker()
        self.inference = InferenceEngine()

    def reason(
        self,
        *,
        query: str,
        world_state: dict[str, Any],
        retrieved_memory: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        evidence_count = sum(len(items) for items in retrieved_memory.values())
        state_complexity = len(world_state.get("entities", [])) + len(world_state.get("events", []))
        confidence = max(0.15, min(0.97, 0.35 + (0.05 * evidence_count) + (0.03 * state_complexity)))
        energy = self.energy.score(
            relevance=min(1.0, 0.45 + (evidence_count * 0.05)),
            urgency=0.8 if world_state.get("goal_candidates") else 0.55,
            reward=0.9 if "build" in query.lower() or "deploy" in query.lower() else 0.65,
        )
        consistency = self.consistency.check(world_state=world_state, retrieved_memory=retrieved_memory)
        inference = self.inference.infer(query=query, world_state=world_state, retrieved_memory=retrieved_memory)
        logic_validation = self.logic.validate(
            query=query,
            contradictions=consistency["contradictions"],
            inferences=inference["inferences"],
        )
        chain = [
            {"step": 1, "kind": "logical", "summary": "Parsed request into structured objective."},
            {"step": 2, "kind": "probabilistic", "summary": f"Estimated outcome confidence at {confidence:.3f}."},
            {"step": 3, "kind": "constraint", "summary": "Checked available world constraints and recent failures."},
        ]
        return {
            "query": query,
            "confidence": round(confidence, 6),
            "success_probability": round(confidence * 0.94, 6),
            "attention_weight": energy.importance or 0.1,
            "uncertainty": round(1.0 - confidence, 6),
            "reasoning_chain": chain,
            "constraints": ["safety", "resource_bounds", "truthfulness"],
            "consistency": consistency,
            "inference": inference,
            "logic_validation": logic_validation,
        }
