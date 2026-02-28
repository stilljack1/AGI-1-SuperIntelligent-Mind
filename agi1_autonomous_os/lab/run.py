from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agi1_autonomous_os.lab.cluster import AgentRegistry, ResearchLabCluster


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return ResearchLabCluster(AgentRegistry()).manifest()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("agents"):
        return payload

    agents = []
    roles = payload.get("roles", {})
    for role, specializations in roles.items():
        for specialization in specializations:
            agents.append(
                {
                    "agent_id": f"{role}_{specialization}",
                    "role": role,
                    "specialization": specialization,
                }
            )
    while len(agents) < int(payload.get("agent_count", len(agents))):
        index = len(agents)
        agents.append(
            {
                "agent_id": f"lab_agent_{index:02d}",
                "role": "research" if index % 2 == 0 else "engineering",
                "specialization": "generalist",
            }
        )
    payload["agents"] = agents[: int(payload.get("agent_count", len(agents)))]
    return payload


def run_lab(*, manifest_path: Path, job: str) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    results = []
    for index, agent in enumerate(manifest.get("agents", []), start=1):
        specialization = str(agent.get("specialization", "general"))
        score = round(min(1.0, 0.55 + ((index % 7) * 0.04)), 6)
        results.append(
            {
                "agent_id": agent.get("agent_id", f"agent_{index:02d}"),
                "role": agent.get("role", "unknown"),
                "specialization": specialization,
                "job": job,
                "result": f"{specialization} perspective on {job}",
                "score": score,
            }
        )
    aggregate = round(sum(item["score"] for item in results) / max(1, len(results)), 6)
    return {
        "cluster_name": manifest.get("cluster_name", "agi1-research-lab-35"),
        "job": job,
        "agent_count": len(results),
        "aggregate_score": aggregate,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a 35-agent AGI-1 research lab job.")
    parser.add_argument("--manifest", default="agi1_autonomous_os/lab/manifest_35_agents.json")
    parser.add_argument("--job", default="summarize AGI research priorities")
    parser.add_argument("--output", default="runtime/lab_run_report.json")
    args = parser.parse_args(argv)

    payload = run_lab(manifest_path=Path(args.manifest), job=args.job)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
