from __future__ import annotations

from dataclasses import dataclass

from .memory_types import MemoryNode


@dataclass(frozen=True)
class BudgetConfig:
    max_nodes_hot: int = 500
    max_nodes_warm: int = 2000
    max_nodes_cold: int = 5000


def prune_candidates(nodes: list[MemoryNode], *, keep: int) -> list[MemoryNode]:
    if len(nodes) <= keep:
        return []
    ranked = sorted(
        nodes,
        key=lambda node: (node.importance, node.confidence, -float(node.access_count)),
    )
    return ranked[: max(0, len(nodes) - keep)]


def compress_candidates(nodes: list[MemoryNode], similarity_threshold: float = 0.97) -> list[tuple[MemoryNode, MemoryNode]]:
    # Lightweight heuristic: same memory_type + identical normalized text
    seen: dict[tuple[str, str], MemoryNode] = {}
    merges: list[tuple[MemoryNode, MemoryNode]] = []
    for node in nodes:
        key = (node.memory_type, " ".join(node.text.lower().split()))
        if key in seen:
            merges.append((seen[key], node))
        else:
            seen[key] = node
    return merges


def enforce_budgets(nodes_by_tier: dict[str, list[MemoryNode]], config: BudgetConfig) -> dict[str, list[MemoryNode]]:
    return {
        "hot_prune": prune_candidates(nodes_by_tier.get("hot", []), keep=config.max_nodes_hot),
        "warm_prune": prune_candidates(nodes_by_tier.get("warm", []), keep=config.max_nodes_warm),
        "cold_prune": prune_candidates(nodes_by_tier.get("cold", []), keep=config.max_nodes_cold),
    }
