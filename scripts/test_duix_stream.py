#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import websockets

PM_LINE = "PM: OpenClaw"
EXEC_LINE = "Exec: Jack | Julia | Singularity | Aegis"


@dataclass
class SessionInfo:
    session_id: str
    token: str
    ws_audio_url: str
    ws_events_url: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 20.0,
    retries: int = 3,
    backoff: float = 0.5,
) -> dict[str, Any]:
    data = None
    headers = {"content-type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url=url, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionResetError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(backoff * attempt)
    assert last_error is not None
    raise RuntimeError(f"http_json_failed:{type(last_error).__name__}:{last_error}") from last_error


def wait_for_health(api_base: str, timeout_sec: float, poll_sec: float = 1.0) -> tuple[bool, str]:
    deadline = time.time() + timeout_sec
    last_error = ""
    while time.time() < deadline:
        try:
            payload = http_json("GET", f"{api_base}/healthz", retries=1, timeout=5.0)
            if payload.get("status") in {"ok", "healthy"}:
                return True, "healthy"
            last_error = f"unexpected_health_payload:{payload}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(poll_sec)
    return False, last_error or "health_timeout"


def create_session(api_base: str, user_id: str, retries: int) -> SessionInfo:
    payload = {"user_id": user_id, "input_lang": "auto", "output_lang": "en", "auto_detect": True}
    data = http_json("POST", f"{api_base}/v1/sessions", payload, retries=retries)
    return SessionInfo(
        session_id=data["session_id"],
        token=data["token"],
        ws_audio_url=data["ws_audio_url"],
        ws_events_url=data["ws_events_url"],
    )


def start_avatar_session(api_base: str, session: SessionInfo, agent_id: str, fps_target: int, retries: int) -> None:
    payload = {
        "session_id": session.session_id,
        "token": session.token,
        "agent_id": agent_id,
        "mode": "realtime_interactive",
        "pip_enabled": True,
        "fps_target": fps_target,
    }
    http_json("POST", f"{api_base}/v1/avatar/session/start", payload, retries=retries)


async def _connect_ws(url: str, retries: int, base_backoff: float) -> websockets.WebSocketClientProtocol:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await websockets.connect(url, max_size=4 * 1024 * 1024)
        except Exception as exc:
            last_error = exc
            if attempt >= retries:
                break
            await asyncio.sleep(base_backoff * attempt)
    assert last_error is not None
    raise RuntimeError(f"websocket_connect_failed:{type(last_error).__name__}:{last_error}") from last_error


def _capture_container_logs(compose_file: Path, output_file: Path) -> str:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "compose", "-f", str(compose_file), "logs", "--tail=300"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        rendered = (proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else "")
        output_file.write_text(rendered, encoding="utf-8")
        return str(output_file)
    except Exception as exc:
        output_file.write_text(f"log_capture_failed:{exc}\n", encoding="utf-8")
        return str(output_file)


def _write_report(report_path: Path, payload: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


async def run_stream_probe(
    api_base: str,
    agent_id: str,
    text: str,
    timeout_sec: float,
    avatar_driver: str,
    retries: int,
) -> tuple[int, dict[str, Any]]:
    health_ok, health_reason = wait_for_health(api_base, timeout_sec=30.0)
    if not health_ok:
        return 2, {"reason": "health_not_ready", "details": health_reason, "next_step": "start_api_and_retry"}

    session = create_session(api_base, user_id="duix-smoke-user", retries=retries)
    start_avatar_session(api_base, session, agent_id=agent_id, fps_target=30, retries=retries)

    ws_audio = f"{session.ws_audio_url}&avatar_driver={avatar_driver}"
    ws_events = session.ws_events_url

    print(PM_LINE)
    print(EXEC_LINE)
    print(f"Session: {session.session_id}")
    print(f"Audio WS:  {ws_audio}")
    print(f"Events WS: {ws_events}")

    required = {"response_text", "visemes", "audio_chunk", "avatar_frame", "voice_quality_gate", "video_quality_gate"}
    seen: dict[str, int] = {}

    events_ws = await _connect_ws(ws_events, retries=retries, base_backoff=0.75)
    audio_ws = await _connect_ws(ws_audio, retries=retries, base_backoff=0.75)
    try:
        await audio_ws.send(
            json.dumps(
                {
                    "type": "text",
                    "text": text,
                    "agent_id": agent_id,
                    "agent_name": agent_id.capitalize(),
                    "style_preset": "executive",
                    "whisper_mode": False,
                    "input_lang": "auto",
                    "output_lang": "en",
                    "current_task": "duix_stream_probe",
                }
            )
        )

        loop = asyncio.get_running_loop()
        end_at = loop.time() + timeout_sec
        while loop.time() < end_at:
            remaining = max(0.01, end_at - loop.time())
            try:
                raw = await asyncio.wait_for(events_ws.recv(), timeout=remaining)
            except asyncio.TimeoutError:
                break
            event = json.loads(raw)
            event_name = str(event.get("event", ""))
            seen[event_name] = seen.get(event_name, 0) + 1
            if required.issubset(set(seen.keys())):
                break
    finally:
        await events_ws.close()
        await audio_ws.close()

    missing = sorted(required.difference(seen.keys()))
    if missing:
        return (
            2,
            {
                "reason": "missing_required_events",
                "missing_events": missing,
                "seen_events": seen,
                "next_step": "check_api_logs_and_avatar_driver",
            },
        )

    return 0, {"reason": "ok", "seen_events": seen}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe AGI1 Duix avatar + lip-sync + voice stream.")
    parser.add_argument("--api-base", default="http://localhost:8080")
    parser.add_argument("--agent-id", default="singularity", choices=["singularity", "jack", "julia"])
    parser.add_argument("--avatar-driver", default="duix", choices=["duix", "avatarify", "dlp3d"])
    parser.add_argument("--timeout-sec", type=float, default=20.0)
    parser.add_argument("--health-timeout-sec", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument(
        "--text",
        default="Run a concise executive update with clear lip sync and voice output.",
    )
    parser.add_argument(
        "--report-path",
        default=str(_repo_root() / "runtime/duix_stream_report.json"),
        help="JSON report path",
    )
    parser.add_argument(
        "--compose-file",
        default=str(_repo_root() / "infra/docker-compose.yml"),
        help="Docker compose file for failure log capture",
    )
    args = parser.parse_args()

    started_at = time.time()
    report_path = Path(args.report_path)
    compose_file = Path(args.compose_file)
    logs_file = _repo_root() / "runtime/duix_stream_container_logs.txt"

    health_ok, health_reason = wait_for_health(args.api_base.rstrip("/"), timeout_sec=args.health_timeout_sec)
    if not health_ok:
        logs_path = _capture_container_logs(compose_file, logs_file)
        payload = {
            "pm": PM_LINE,
            "exec": EXEC_LINE,
            "status": "FAIL",
            "reason": "health_not_ready",
            "details": health_reason,
            "next_step": "run docker compose -f infra/docker-compose.yml up -d then rerun this script",
            "logs_path": logs_path,
            "duration_s": round(time.time() - started_at, 3),
        }
        _write_report(report_path, payload)
        print(json.dumps(payload, indent=2))
        return 2

    try:
        code, details = asyncio.run(
            run_stream_probe(
                api_base=args.api_base.rstrip("/"),
                agent_id=args.agent_id,
                text=args.text,
                timeout_sec=args.timeout_sec,
                avatar_driver=args.avatar_driver,
                retries=max(1, args.retries),
            )
        )
        status = "PASS" if code == 0 else "FAIL"
        logs_path = ""
        if status != "PASS":
            logs_path = _capture_container_logs(compose_file, logs_file)
        payload = {
            "pm": PM_LINE,
            "exec": EXEC_LINE,
            "status": status,
            "details": details,
            "next_step": "stream_probe_complete" if status == "PASS" else details.get("next_step", "inspect_logs"),
            "logs_path": logs_path,
            "duration_s": round(time.time() - started_at, 3),
        }
        _write_report(report_path, payload)
        print(json.dumps(payload, indent=2))
        return code
    except Exception as exc:
        logs_path = _capture_container_logs(compose_file, logs_file)
        payload = {
            "pm": PM_LINE,
            "exec": EXEC_LINE,
            "status": "FAIL",
            "reason": "probe_exception",
            "details": str(exc),
            "next_step": "inspect_report_and_logs_then_restart_api_and_media",
            "logs_path": logs_path,
            "duration_s": round(time.time() - started_at, 3),
        }
        _write_report(report_path, payload)
        print(json.dumps(payload, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
