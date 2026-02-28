#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
AGI_CORE = ROOT / "agi-core"
for candidate in (ROOT, AGI_CORE):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from runtime.message_protocol import MessageBus  # noqa: E402
from agi1.supervisors.simulate import run_simulation  # noqa: E402
from agi1_autonomous_os.lab.run import run_lab  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def probe_http(url: str, *, timeout_s: float = 5.0) -> dict[str, Any]:
    request = Request(url=url, method="GET")
    try:
        with urlopen(request, timeout=timeout_s) as response:
            body = response.read(256)
            return {
                "url": url,
                "http_status": int(response.status),
                "ok": int(response.status) == 200,
                "body_preview": body.decode("utf-8", errors="replace"),
            }
    except URLError as exc:
        return {"url": url, "http_status": 0, "ok": False, "error": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive
        return {"url": url, "http_status": 0, "ok": False, "error": str(exc)}


def probe_port(host: str, port: int, *, timeout_s: float = 2.5) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_s)
    try:
        sock.connect((host, port))
    except Exception:
        return "closed"
    finally:
        sock.close()
    return "open"


def build_bridge_report(host: str, status_port: int, stream_port: int) -> dict[str, Any]:
    paths = ["/status", "/health", "/api/status", "/"]
    http_checks = [probe_http(f"http://{host}:{status_port}{path}") for path in paths]
    healthy = next((check for check in http_checks if check.get("http_status") == 200), None)
    return {
        "host": host,
        "status_port": status_port,
        "stream_port": stream_port,
        "http_checks": http_checks,
        "ports": {
            str(status_port): probe_port(host, status_port),
            str(stream_port): probe_port(host, stream_port),
        },
        "healthy_endpoint": healthy["url"] if healthy else "",
        "heartbeat_ok": healthy is not None,
    }


def exchange_render_railway_messages(*, bus: MessageBus, supervisor_report: dict[str, Any], lab_report: dict[str, Any]) -> dict[str, Any]:
    bus.publish(
        sender="render_backend",
        receiver="railway_avatar",
        intent="context_bundle",
        data={
            "consensus_success_pct": supervisor_report["consensus_success_pct"],
            "leader_changes": supervisor_report["leader_changes"],
            "lab_job": lab_report["job"],
        },
        confidence=0.93,
        priority=0.88,
    )
    bus.publish(
        sender="railway_avatar",
        receiver="render_backend",
        intent="avatar_sync",
        data={
            "cluster_name": lab_report["cluster_name"],
            "aggregate_score": lab_report["aggregate_score"],
            "agent_count": lab_report["agent_count"],
        },
        confidence=0.89,
        priority=0.84,
    )
    bus.publish(
        sender="render_backend",
        receiver="railway_avatar",
        intent="alignment_review",
        data={"status": "proceed_if_bridge_healthy"},
        confidence=0.97,
        priority=0.95,
    )
    return {
        "railway_inbox": bus.dispatch(receiver="railway_avatar"),
        "render_inbox": bus.dispatch(receiver="render_backend"),
    }


def remote_build_status() -> dict[str, Any]:
    railway_key = bool(os.getenv("RAILWAY_API_KEY", "").strip())
    render_key = bool(os.getenv("RENDER_API_KEY", "").strip())
    return {
        "railway": {
            "can_query": railway_key,
            "status": "ready" if railway_key else "blocked_missing_api_key",
        },
        "render": {
            "can_query": render_key,
            "status": "ready" if render_key else "blocked_missing_api_key",
        },
    }


def consensus_status(report: dict[str, Any]) -> str:
    if report["consensus_success_pct"] >= 99.0 and report["success_rate"] >= 0.95:
        return "ALIGNED"
    if report["consensus_success_pct"] >= 90.0:
        return "PARTIAL_ALIGNMENT"
    return "DEGRADED"


def orchestrate(*, supervisors: int, duration: int, bridge_host: str, status_port: int, stream_port: int, job: str) -> dict[str, Any]:
    supervisor_report = run_simulation(total=supervisors, duration=duration)
    lab_report = run_lab(
        manifest_path=ROOT / "agi1_autonomous_os" / "lab" / "manifest_35_agents.json",
        job=job,
    )
    bus = MessageBus()
    bridge_report = build_bridge_report(bridge_host, status_port, stream_port)
    message_exchange = exchange_render_railway_messages(
        bus=bus,
        supervisor_report=supervisor_report,
        lab_report=lab_report,
    )
    return {
        "computed_at": utc_now(),
        "supervisors": supervisor_report,
        "consensus_status": consensus_status(supervisor_report),
        "research_lab": lab_report,
        "bridge": bridge_report,
        "render_railway_bus": message_exchange,
        "remote_builds": remote_build_status(),
        "self_heal_status": {
            "ready": False,
            "reason": "remote build mutation requires authenticated Railway/Render credentials and deploy authority",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AGI-1 autonomous orchestration.")
    parser.add_argument("--supervisors", type=int, default=1000)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--bridge-host", default="18.227.183.151")
    parser.add_argument("--status-port", type=int, default=8080)
    parser.add_argument("--stream-port", type=int, default=5000)
    parser.add_argument("--job", default="process 30-page platform logic")
    parser.add_argument("--output", default="runtime/autonomous_orchestration_report.json")
    args = parser.parse_args(argv)

    payload = orchestrate(
        supervisors=max(1, args.supervisors),
        duration=max(1, args.duration),
        bridge_host=args.bridge_host,
        status_port=args.status_port,
        stream_port=args.stream_port,
        job=args.job,
    )
    output_path = ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
