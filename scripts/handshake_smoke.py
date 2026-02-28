from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "core" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "memory" / "voice_profiles" / "src"))
sys.path.insert(0, str(ROOT / "packages"))


def _headers(*, nonce: str, user_id: str, handshake: str = "") -> dict[str, str]:
    payload = {
        "X-API-Key": "smoke-api-key",
        "X-OpenClaw-Timestamp": str(int(time.time())),
        "X-OpenClaw-Nonce": nonce,
        "X-AGI1-User": user_id,
    }
    if handshake:
        payload["X-AGI1-Handshake"] = handshake
    return payload


def run_smoke() -> dict[str, object]:
    os.environ["OPENCLAW_REQUIRE_AUTH"] = "true"
    os.environ["OPENCLAW_REQUIRE_REPLAY"] = "true"
    os.environ["OPENCLAW_API_KEY"] = "smoke-api-key"
    os.environ["AGI1_REQUIRE_HANDSHAKE"] = "true"
    os.environ.setdefault("MEDIA_URL", "http://127.0.0.1:9999")
    os.environ.setdefault("DATA_DIR", str(ROOT / ".tmp_test_data"))
    os.environ["AGI1_HANDSHAKE_STATE_PATH"] = str(ROOT / ".tmp_test_data" / "handshake_state_smoke.json")
    os.environ["AGI1_TASK_RUNTIME_STATE_PATH"] = str(ROOT / ".tmp_test_data" / "task_runtime_smoke.json")

    for module_name in list(sys.modules.keys()):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        user_id = "smoke-user"
        without_token = client.post(
            "/v1/tasks",
            json={"actor": "jack", "user_message": "smoke", "priority": "normal", "mode": "staging"},
            headers=_headers(nonce=f"no-token-{uuid.uuid4().hex}", user_id=user_id),
        )

        attest = client.post(
            "/v1/handshake/attest",
            json={"camera": True, "mic": True, "data": True, "client_ts": int(time.time() * 1000), "version": "v1"},
            headers=_headers(nonce=f"attest-{uuid.uuid4().hex}", user_id=user_id),
        )
        handshake_token = attest.json().get("handshake_token", "") if attest.status_code < 400 else ""

        with_token = client.post(
            "/v1/tasks",
            json={"actor": "jack", "user_message": "smoke-ok", "priority": "normal", "mode": "staging"},
            headers=_headers(nonce=f"with-token-{uuid.uuid4().hex}", user_id=user_id, handshake=handshake_token),
        )

    checks = {
        "handshake_required": without_token.status_code == 403 and without_token.json().get("detail", {}).get("error") == "HANDSHAKE_REQUIRED",
        "attest_issued": attest.status_code == 200 and bool(handshake_token),
        "handshake_allows": with_token.status_code == 200 and bool(with_token.json().get("task_id")),
    }
    return {
        "status": "ok" if all(checks.values()) else "no-go",
        "checks": checks,
        "codes": {
            "without_handshake": without_token.status_code,
            "attest": attest.status_code,
            "with_handshake": with_token.status_code,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sovereign Handshake smoke checks.")
    parser.add_argument("--output", default="", help="Optional path to write JSON report.")
    args = parser.parse_args()
    result = run_smoke()
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
