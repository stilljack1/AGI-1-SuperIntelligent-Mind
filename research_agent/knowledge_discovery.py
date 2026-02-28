from __future__ import annotations


class KnowledgeDiscovery:
    def discover(self, experiment: dict[str, object]) -> dict[str, object]:
        return {
            "finding": "reversible actions improve stability under uncertainty",
            "supporting_metrics": experiment.get("metrics", []),
        }
