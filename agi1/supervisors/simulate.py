from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name("1000_agent_network.py")
SPEC = importlib.util.spec_from_file_location("agi1.supervisors.network1000", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable_to_load_supervisor_network_module")
NETWORK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = NETWORK
SPEC.loader.exec_module(NETWORK)

SwarmMessageBus = NETWORK.SwarmMessageBus
bootstrap_supervisors = NETWORK.bootstrap_supervisors
detect_failures = NETWORK.detect_failures
elect_leader = NETWORK.elect_leader


def run_simulation(*, total: int, duration: int) -> dict[str, object]:
    nodes = bootstrap_supervisors(total)
    bus = SwarmMessageBus()
    leader_changes = 0
    consensus_rounds = 0
    previous_leader = ""
    timeout_events = 0

    for tick in range(1, duration + 1):
        for index, node in enumerate(nodes):
            if (index + tick) % 23 != 0:
                node.heartbeat(now_epoch=float(tick))
        if tick > max(2, duration // 3):
            for node in nodes[::37]:
                node.last_heartbeat_epoch = float(tick - 40)
        failed = detect_failures(nodes, now_epoch=float(tick), timeout_s=15.0)
        timeout_events += len(failed)
        leader = elect_leader(nodes)
        if leader is not None:
            consensus_rounds += 1
            if previous_leader and previous_leader != leader.supervisor_id:
                leader_changes += 1
            previous_leader = leader.supervisor_id
            bus.publish(sender_id=leader.supervisor_id, event="consensus_round", payload={"tick": tick})

    alive = sum(1 for node in nodes if node.alive)
    success_rate = alive / max(1, total)
    return {
        "supervisors": total,
        "duration_s": duration,
        "alive": alive,
        "success_rate": round(success_rate, 6),
        "timeouts": timeout_events,
        "leader_changes": leader_changes,
        "consensus_success_pct": round((consensus_rounds / max(1, duration)) * 100.0, 6),
        "recent_messages": bus.recent(limit=10),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AGI-1 supervisor swarm simulation.")
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--output", default="runtime/supervisor_simulation.json")
    args = parser.parse_args(argv)

    payload = run_simulation(total=max(1, args.n), duration=max(1, args.duration))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
