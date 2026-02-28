from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class LabAgent:
    agent_id: str
    role: str
    specialization: str


class AgentRegistry:
    def __init__(self) -> None:
        roles = [
            ("research", "evaluation"),
            ("research", "benchmarking"),
            ("research", "planning"),
            ("engineering", "runtime"),
            ("engineering", "memory"),
            ("engineering", "safety"),
            ("engineering", "mobile"),
        ]
        self._agents = [
            LabAgent(agent_id=f"lab_agent_{index:02d}", role=roles[index % len(roles)][0], specialization=roles[index % len(roles)][1])
            for index in range(35)
        ]

    def all(self) -> list[LabAgent]:
        return list(self._agents)


class ResearchLabCluster:
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or AgentRegistry()

    def manifest(self) -> dict[str, object]:
        agents = [asdict(agent) for agent in self.registry.all()]
        return {
            "cluster_name": "agi1-research-lab-35",
            "agent_count": len(agents),
            "agents": agents,
        }
