from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agi1_autonomous_os.gateways.messaging_bridge import (  # noqa: E402
    AGICLIRunner,
    CLIRunResult,
    MessagingBridge,
    MessagingBridgeConfig,
    build_messaging_app,
)
from agi1_autonomous_os.orchestrator.openclaw_telemetry import (  # noqa: E402
    OpenClawTelemetryBridge,
    TelemetrySecurityConfig,
    build_telemetry_app,
)


@dataclass(frozen=True)
class ProbeConfig:
    telemetry_api_key: str
    webhook_secret: str
    ceo_telegram_user_id: str
    ceo_whatsapp_number: str


class ProbeCLIRunner(AGICLIRunner):
    async def run(self, *, task: str) -> CLIRunResult:
        trimmed = task.strip()[:140]
        return CLIRunResult(
            exit_code=0,
            stdout=f"Executed: {trimmed}",
            stderr="",
            audit_path="/tmp/openclaw_probe_audit.json",
        )


class ProbeMessagingBridge(MessagingBridge):
    async def _send_telegram_message(self, *, chat_id: str, text: str) -> None:
        return None


def _signature(secret_key: str, raw_body: bytes, timestamp: str, nonce: str) -> str:
    signed_payload = f"{timestamp}.{nonce}.".encode("utf-8") + raw_body
    return hmac.new(secret_key.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()


async def _record_telemetry(
    telemetry: OpenClawTelemetryBridge,
    *,
    provider: str,
    summary: dict[str, Any],
    task_id: str,
) -> None:
    text = str(summary.get("command", ""))
    output_size = len(str(summary.get("cli_stdout", "")))
    status = "completed" if int(summary.get("cli_exit_code", 1)) == 0 else "failed"
    decision = str(summary.get("aegis_validation", "warning"))

    await telemetry.record_workflow_transition(
        stage=f"messaging:{provider}:received",
        agent_id="julia",
        task_id=task_id,
        metadata={"provider": provider},
    )
    await telemetry.record_token_consumption(
        agent_id="jack",
        input_tokens=max(1, len(text.split()) * 12),
        output_tokens=max(1, output_size // 4),
        execution_cost_usd=0.0001,
        task_id=task_id,
        metadata={"provider": provider},
    )
    if decision == "blocked":
        await telemetry.record_aegis_intervention(decision="block", task_id=task_id, reason="consensus_block")
    elif decision == "warning":
        await telemetry.record_aegis_intervention(decision="warning", task_id=task_id, reason="cli_nonzero")
    else:
        await telemetry.record_aegis_intervention(decision="approval", task_id=task_id, reason="consensus_ok")

    await telemetry.record_singularity_event(
        event_type="self_improvement_trigger",
        task_id=task_id,
        metadata={"provider": provider},
    )
    await telemetry.record_singularity_event(
        event_type="memory_consolidation",
        task_id=task_id,
        metadata={"provider": provider},
    )
    await telemetry.record_task_outcome(status=status, task_id=task_id, metadata={"provider": provider})


def run_probe(config: ProbeConfig) -> dict[str, Any]:
    telemetry_bridge = OpenClawTelemetryBridge()
    telemetry_app = build_telemetry_app(
        bridge=telemetry_bridge,
        security=TelemetrySecurityConfig(api_key=config.telemetry_api_key),
    )

    messaging_config = MessagingBridgeConfig(
        telegram_bot_token="probe-token",
        ceo_telegram_user_id=config.ceo_telegram_user_id,
        ceo_whatsapp_number=config.ceo_whatsapp_number,
        webhook_secret=config.webhook_secret,
        agi_cli_bin="agi",
        work_dir=str(ROOT),
        command_timeout_seconds=120,
        strict_secrets=False,
    )
    bridge = ProbeMessagingBridge(config=messaging_config, cli_runner=ProbeCLIRunner())
    messaging_app = build_messaging_app(bridge=bridge)

    report: dict[str, Any] = {
        "pm": "OpenClaw",
        "exec": "Agent 1 Jack | Agent 2 Julia | Agent 3 Singularity | Agent 4 Aegis",
        "steps": [],
    }

    with TestClient(messaging_app) as messaging_client, TestClient(telemetry_app) as telemetry_client:
        telegram_payload = {
            "message": {
                "from": {"id": int(config.ceo_telegram_user_id)},
                "chat": {"id": int(config.ceo_telegram_user_id)},
                "text": "Analyze live dataset, write deployment script, calculate market ROI.",
            }
        }
        telegram_body = json.dumps(telegram_payload).encode("utf-8")
        telegram_ts = str(int(time.time()))
        telegram_nonce = secrets.token_hex(8)
        telegram_sig = _signature(config.webhook_secret, telegram_body, telegram_ts, telegram_nonce)
        telegram_response = messaging_client.post(
            "/v1/openclaw/webhook/telegram",
            data=telegram_body,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": telegram_sig,
                "X-OpenClaw-Timestamp": telegram_ts,
                "X-OpenClaw-Nonce": telegram_nonce,
            },
        )
        if telegram_response.status_code != 200:
            raise RuntimeError(f"Telegram probe failed: {telegram_response.status_code} {telegram_response.text}")
        telegram_summary = telegram_response.json()
        asyncio.run(_record_telemetry(telemetry_bridge, provider="telegram", summary=telegram_summary, task_id="probe-tg-1"))
        report["steps"].append({"name": "telegram_webhook", "status": "ok", "result": telegram_summary})

        whatsapp_payload = {
            "From": config.ceo_whatsapp_number,
            "Body": "Execute AGI run for pricing model synthesis with safety checks.",
        }
        whatsapp_body = json.dumps(whatsapp_payload).encode("utf-8")
        whatsapp_ts = str(int(time.time()))
        whatsapp_nonce = secrets.token_hex(8)
        whatsapp_sig = _signature(config.webhook_secret, whatsapp_body, whatsapp_ts, whatsapp_nonce)
        whatsapp_response = messaging_client.post(
            "/v1/openclaw/webhook/whatsapp",
            data=whatsapp_body,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": whatsapp_sig,
                "X-OpenClaw-Timestamp": whatsapp_ts,
                "X-OpenClaw-Nonce": whatsapp_nonce,
            },
        )
        if whatsapp_response.status_code != 200:
            raise RuntimeError(f"WhatsApp probe failed: {whatsapp_response.status_code} {whatsapp_response.text}")
        whatsapp_summary = whatsapp_response.json()
        asyncio.run(
            _record_telemetry(telemetry_bridge, provider="whatsapp", summary=whatsapp_summary, task_id="probe-wa-1")
        )
        report["steps"].append({"name": "whatsapp_webhook", "status": "ok", "result": whatsapp_summary})

        telemetry_response = telemetry_client.get(
            "/v1/openclaw/telemetry",
            headers={"X-OpenClaw-Api-Key": config.telemetry_api_key},
        )
        if telemetry_response.status_code != 200:
            raise RuntimeError(f"Telemetry read failed: {telemetry_response.status_code} {telemetry_response.text}")
        telemetry_snapshot = telemetry_response.json()
        if int(telemetry_snapshot.get("total_events", 0)) < 6:
            raise RuntimeError("Telemetry snapshot did not persist expected events.")
        report["steps"].append(
            {
                "name": "telemetry_read",
                "status": "ok",
                "result": {
                    "total_events": telemetry_snapshot["total_events"],
                    "task_success_rate": telemetry_snapshot["tasks"]["success_rate"],
                    "aegis_intervention_rate": telemetry_snapshot["aegis"]["intervention_rate"],
                },
            }
        )

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw production E2E probe (local deterministic run).")
    parser.add_argument("--telemetry-api-key", default=os.getenv("OPENCLAW_TELEMETRY_API_KEY", "probe-telemetry-key"))
    parser.add_argument("--webhook-secret", default=os.getenv("OPENCLAW_WEBHOOK_SECRET", "probe-webhook-secret"))
    parser.add_argument("--ceo-telegram-id", default=os.getenv("OPENCLAW_CEO_TELEGRAM_ID", "10001"))
    parser.add_argument("--ceo-whatsapp", default=os.getenv("OPENCLAW_CEO_WHATSAPP_NUMBER", "+15550001111"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ProbeConfig(
        telemetry_api_key=args.telemetry_api_key,
        webhook_secret=args.webhook_secret,
        ceo_telegram_user_id=str(args.ceo_telegram_id),
        ceo_whatsapp_number=str(args.ceo_whatsapp),
    )
    report = run_probe(config)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
