from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .memory_types import MemoryNode


EXECUTIVE_AGENTS = {"jack", "julia", "singularity", "aegis"}


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str


class MemoryAccessController:
    def __init__(self) -> None:
        self._agent_roles = {
            "jack": {"exec", "advisor"},
            "julia": {"exec", "advisor"},
            "singularity": {"exec", "operator"},
            "aegis": {"exec", "safety"},
        }

    def roles_for_agent(self, agent_id: str) -> set[str]:
        return set(self._agent_roles.get(agent_id, {"worker"}))

    def can_write(
        self,
        *,
        target_user_id: str,
        request_user_id: str,
        request_agent_id: str,
        privacy: str,
    ) -> AccessDecision:
        if request_user_id != target_user_id and request_user_id != "global":
            return AccessDecision(False, "cross_user_write_forbidden")
        if privacy == "public" and request_agent_id not in EXECUTIVE_AGENTS:
            return AccessDecision(False, "public_write_requires_executive")
        return AccessDecision(True, "ok")

    def can_read(
        self,
        node: MemoryNode,
        *,
        request_user_id: str,
        request_agent_id: str,
    ) -> AccessDecision:
        if node.user_id not in {request_user_id, "global"}:
            return AccessDecision(False, "cross_user_read_forbidden")

        if node.privacy == "public":
            return AccessDecision(True, "ok")

        if node.privacy == "private":
            if request_user_id == node.user_id and request_agent_id == node.agent_id:
                return AccessDecision(True, "ok")
            if request_agent_id == "aegis":
                return AccessDecision(True, "aegis_audit_read")
            return AccessDecision(False, "private_memory_scope")

        allowed_agents = set(node.policy.get("allowed_agents", []))
        if allowed_agents and request_agent_id not in allowed_agents:
            return AccessDecision(False, "shared_policy_agent_block")

        allowed_roles = set(node.policy.get("allowed_roles", []))
        if allowed_roles:
            agent_roles = self.roles_for_agent(request_agent_id)
            if allowed_roles.isdisjoint(agent_roles):
                return AccessDecision(False, "shared_policy_role_block")

        return AccessDecision(True, "ok")

    def filter_readable(
        self,
        nodes: Iterable[MemoryNode],
        *,
        request_user_id: str,
        request_agent_id: str,
    ) -> list[MemoryNode]:
        readable: list[MemoryNode] = []
        for node in nodes:
            decision = self.can_read(
                node,
                request_user_id=request_user_id,
                request_agent_id=request_agent_id,
            )
            if decision.allowed:
                readable.append(node)
        return readable
