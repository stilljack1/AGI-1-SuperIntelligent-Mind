#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="18.227.183.151"
STATUS_PORT="8080"
STREAM_PORT="5000"
STATUS_PATH="/status"
OUTPUT_PATH="$ROOT_DIR/runtime/bridge_health_report.json"
RESTART_ON_FAIL=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/verify_bridge_health.sh [options]

Check the AGI-1 bridge status endpoint and TCP reachability for signaling/stream ports.

Options:
  --host HOST            Bridge host or IP (default: 18.227.183.151)
  --status-port PORT     HTTP signaling/status port (default: 8080)
  --stream-port PORT     Stream port (default: 5000)
  --status-path PATH     HTTP health path (default: /status)
  --output PATH          JSON report output path
  --restart-on-fail      Run ./start.sh locally if the status check is non-200
  -h, --help             Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --status-port)
      STATUS_PORT="${2:-}"
      shift 2
      ;;
    --stream-port)
      STREAM_PORT="${2:-}"
      shift 2
      ;;
    --status-path)
      STATUS_PATH="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --restart-on-fail)
      RESTART_ON_FAIL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

mkdir -p "$(dirname "$OUTPUT_PATH")"

STATUS_URL="http://${HOST}:${STATUS_PORT}${STATUS_PATH}"
HTTP_CODE="000"
STATUS_ERROR=""

if command -v curl >/dev/null 2>&1; then
  if ! HTTP_CODE="$(curl -sS -o /tmp/agi1_bridge_status_body.txt -w "%{http_code}" --max-time 10 "$STATUS_URL" 2>/tmp/agi1_bridge_status_error.txt)"; then
    HTTP_CODE="000"
    STATUS_ERROR="$(cat /tmp/agi1_bridge_status_error.txt 2>/dev/null || true)"
  fi
else
  STATUS_ERROR="curl_not_installed"
fi

check_port() {
  local host="$1"
  local port="$2"
  python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
try:
    sock.connect((host, port))
except Exception:
    print("closed")
    sys.exit(1)
else:
    print("open")
    sys.exit(0)
finally:
    sock.close()
PY
}

SIGNALING_STATE="closed"
STREAM_STATE="closed"
if SIGNALING_STATE="$(check_port "$HOST" "$STATUS_PORT" 2>/dev/null)"; then
  :
fi
if STREAM_STATE="$(check_port "$HOST" "$STREAM_PORT" 2>/dev/null)"; then
  :
fi

RESTART_TRIGGERED=0
if [[ "$HTTP_CODE" != "200" && "$RESTART_ON_FAIL" -eq 1 && -x "$ROOT_DIR/start.sh" ]]; then
  "$ROOT_DIR/start.sh" >/tmp/agi1_bridge_restart.log 2>&1 || true
  RESTART_TRIGGERED=1
fi

python3 - "$OUTPUT_PATH" "$HOST" "$STATUS_URL" "$HTTP_CODE" "$STATUS_ERROR" "$SIGNALING_STATE" "$STREAM_STATE" "$RESTART_TRIGGERED" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

output_path, host, status_url, http_code, status_error, signaling_state, stream_state, restart_triggered = sys.argv[1:]
payload = {
    "pm": "PM: OpenClaw",
    "exec": "Exec: Jack | Julia | Singularity | Aegis",
    "host": host,
    "status_url": status_url,
    "http_status": http_code,
    "status_ok": http_code == "200",
    "status_error": status_error,
    "ports": {
        "8080": signaling_state,
        "5000": stream_state,
    },
    "restart_triggered": restart_triggered == "1",
    "computed_at": datetime.now(timezone.utc).isoformat(),
}
path = pathlib.Path(output_path)
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
sys.exit(0 if payload["status_ok"] else 1)
PY
