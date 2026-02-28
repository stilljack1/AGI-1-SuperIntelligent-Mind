from __future__ import annotations

import hashlib
import hmac
import json
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


class _Runner(AGICLIRunner):
    async def run(self, *, task: str) -> CLIRunResult:
        return CLIRunResult(exit_code=0, stdout=f"ok:{task[:40]}", stderr="", audit_path="/tmp/attack-audit.json")


class _BridgeNoOutbound(MessagingBridge):
    async def _send_telegram_message(self, *, chat_id: str, text: str) -> None:
        return None


def _signature(secret_key: str, raw_body: bytes, timestamp: str, nonce: str) -> str:
    signed_payload = f"{timestamp}.{nonce}.".encode("utf-8") + raw_body
    return hmac.new(secret_key.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class AttackCase:
    name: str
    status_code: int
    detail_contains: str


def _assert_case(case: AttackCase, response_body: dict[str, Any], status_code: int) -> None:
    if status_code != case.status_code:
        raise AssertionError(f"{case.name}: status {status_code}, expected {case.status_code}")
    detail = str(response_body.get("detail", ""))
    if case.detail_contains and case.detail_contains not in detail:
        raise AssertionError(f"{case.name}: detail {detail!r} does not contain {case.detail_contains!r}")
    print(f"[PASS] {case.name} -> {status_code}")


def main() -> None:
    secret = "attack-test-secret"
    config = MessagingBridgeConfig(
        telegram_bot_token="token",
        ceo_telegram_user_id="10001",
        ceo_whatsapp_number="+15550001111",
        webhook_secret=secret,
        agi_cli_bin="agi",
        work_dir=str(ROOT),
        command_timeout_seconds=60,
        strict_secrets=False,
        max_payload_bytes=256,
        replay_window_seconds=60,
        webhook_rate_capacity=100,
        webhook_rate_refill_per_sec=10.0,
        sender_rate_capacity=2,
        sender_rate_refill_per_sec=0.1,
    )
    app = build_messaging_app(bridge=_BridgeNoOutbound(config=config, cli_runner=_Runner()))

    with TestClient(app) as client:
        payload = {
            "message": {
                "from": {"id": 10001},
                "chat": {"id": 10001},
                "text": "run safe command",
            }
        }
        raw_body = json.dumps(payload).encode("utf-8")
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(8)

        invalid_sig_resp = client.post(
            "/v1/openclaw/webhook/telegram",
            data=raw_body,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": "bad-signature",
                "X-OpenClaw-Timestamp": timestamp,
                "X-OpenClaw-Nonce": nonce,
            },
        )
        _assert_case(
            AttackCase("invalid_signature_rejected", 403, "Webhook signature mismatch"),
            invalid_sig_resp.json(),
            invalid_sig_resp.status_code,
        )

        good_sig = _signature(secret, raw_body, timestamp, nonce)
        valid_resp = client.post(
            "/v1/openclaw/webhook/telegram",
            data=raw_body,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": good_sig,
                "X-OpenClaw-Timestamp": timestamp,
                "X-OpenClaw-Nonce": nonce,
            },
        )
        if valid_resp.status_code != 200:
            raise AssertionError(f"valid request failed unexpectedly: {valid_resp.status_code} {valid_resp.text}")
        print("[PASS] valid_request_allowed -> 200")

        replay_resp = client.post(
            "/v1/openclaw/webhook/telegram",
            data=raw_body,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": good_sig,
                "X-OpenClaw-Timestamp": timestamp,
                "X-OpenClaw-Nonce": nonce,
            },
        )
        _assert_case(
            AttackCase("replay_nonce_blocked", 403, "Replay nonce detected"),
            replay_resp.json(),
            replay_resp.status_code,
        )

        oversized_payload = {
            "message": {
                "from": {"id": 10001},
                "chat": {"id": 10001},
                "text": "X" * 800,
            }
        }
        oversized_raw = json.dumps(oversized_payload).encode("utf-8")
        oversized_ts = str(int(time.time()))
        oversized_nonce = secrets.token_hex(8)
        oversized_sig = _signature(secret, oversized_raw, oversized_ts, oversized_nonce)
        oversized_resp = client.post(
            "/v1/openclaw/webhook/telegram",
            data=oversized_raw,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": oversized_sig,
                "X-OpenClaw-Timestamp": oversized_ts,
                "X-OpenClaw-Nonce": oversized_nonce,
            },
        )
        _assert_case(
            AttackCase("payload_size_limited", 403, "Payload too large"),
            oversized_resp.json(),
            oversized_resp.status_code,
        )

        unauthorized_payload = {
            "message": {
                "from": {"id": 77777},
                "chat": {"id": 77777},
                "text": "attempt execution",
            }
        }
        unauthorized_raw = json.dumps(unauthorized_payload).encode("utf-8")
        unauthorized_ts = str(int(time.time()))
        unauthorized_nonce = secrets.token_hex(8)
        unauthorized_sig = _signature(secret, unauthorized_raw, unauthorized_ts, unauthorized_nonce)
        unauthorized_resp = client.post(
            "/v1/openclaw/webhook/telegram",
            data=unauthorized_raw,
            headers={
                "content-type": "application/json",
                "X-OpenClaw-Signature": unauthorized_sig,
                "X-OpenClaw-Timestamp": unauthorized_ts,
                "X-OpenClaw-Nonce": unauthorized_nonce,
            },
        )
        _assert_case(
            AttackCase("sender_auth_enforced", 403, "Unauthorized Telegram sender"),
            unauthorized_resp.json(),
            unauthorized_resp.status_code,
        )

        base_ts = str(int(time.time()))
        for i in range(3):
            nonce_i = secrets.token_hex(8)
            sig_i = _signature(secret, raw_body, base_ts, nonce_i)
            rate_resp = client.post(
                "/v1/openclaw/webhook/telegram",
                data=raw_body,
                headers={
                    "content-type": "application/json",
                    "X-OpenClaw-Signature": sig_i,
                    "X-OpenClaw-Timestamp": base_ts,
                    "X-OpenClaw-Nonce": nonce_i,
                },
            )
            if i < 1 and rate_resp.status_code != 200:
                raise AssertionError(f"rate-limit setup request failed unexpectedly: {rate_resp.status_code}")
            if i >= 1:
                _assert_case(
                    AttackCase("rate_limit_enforced", 403, "rate limit exceeded"),
                    rate_resp.json(),
                    rate_resp.status_code,
                )
                break

    print("PM: OpenClaw")
    print("Exec: Agent 1 Jack | Agent 2 Julia | Agent 3 Singularity | Agent 4 Aegis")
    print("Security attack suite completed.")


if __name__ == "__main__":
    main()
