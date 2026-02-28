from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentNode:
    agent_id: str
    tier: str


@dataclass
class SupervisorNode:
    supervisor_id: str
    tier: str
    alive: bool = True
    assigned_tasks: list[str] | None = None
    last_heartbeat_epoch: float = 0.0

    def __post_init__(self) -> None:
        if self.assigned_tasks is None:
            self.assigned_tasks = []

    def assign(self, task_id: str) -> None:
        self.assigned_tasks.append(task_id)

    def heartbeat(self, now_epoch: float) -> None:
        self.last_heartbeat_epoch = now_epoch
        self.alive = True


class SwarmMessageBus:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def publish(self, *, sender_id: str, event: str, payload: dict[str, Any]) -> None:
        self.messages.append({"sender_id": sender_id, "event": event, "payload": payload})

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self.messages[-limit:]


def build_network(total: int = 1000) -> list[AgentNode]:
    agents: list[AgentNode] = []
    for index in range(total):
        if index < 10:
            tier = "executive"
        elif index < 100:
            tier = "vp"
        else:
            tier = "manager"
        agents.append(AgentNode(agent_id=f"agent_{index:04d}", tier=tier))
    return agents


def bootstrap_supervisors(total: int = 1000) -> list[SupervisorNode]:
    return [SupervisorNode(supervisor_id=f"sup_{index:04d}", tier=node.tier) for index, node in enumerate(build_network(total))]


def elect_leader(nodes: list[SupervisorNode]) -> SupervisorNode | None:
    alive = [node for node in nodes if node.alive]
    if not alive:
        return None
    return min(alive, key=lambda node: node.supervisor_id)


def detect_failures(nodes: list[SupervisorNode], *, now_epoch: float, timeout_s: float = 15.0) -> list[str]:
    failed = []
    for node in nodes:
        if node.last_heartbeat_epoch and (now_epoch - node.last_heartbeat_epoch) > timeout_s:
            node.alive = False
            failed.append(node.supervisor_id)
    return failed


def simulate_swarm(total: int = 1000) -> dict[str, Any]:
    nodes = bootstrap_supervisors(total)
    bus = SwarmMessageBus()
    for index, node in enumerate(nodes[:35]):
        node.assign(f"task_{index:04d}")
        node.heartbeat(now_epoch=1000.0 + index)
        bus.publish(sender_id=node.supervisor_id, event="task_assigned", payload={"task_id": f"task_{index:04d}"})
    leader = elect_leader(nodes)
    failed = detect_failures(nodes, now_epoch=1030.0, timeout_s=20.0)
    return {
        "total_supervisors": total,
        "leader": leader.supervisor_id if leader is not None else "",
        "failed_nodes": failed,
        "assigned_nodes": sum(1 for node in nodes if node.assigned_tasks),
        "messages": bus.recent(limit=10),
    }
