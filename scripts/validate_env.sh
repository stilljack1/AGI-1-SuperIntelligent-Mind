#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK_DIR="$ROOT_DIR/agi1"
MODE="staging"
ENV_FILE=""
OUTPUT_PATH=""

default_env_file() {
  if [[ "$MODE" == "production" ]]; then
    printf '%s\n' "$HOME/.agi1/production.env"
  else
    printf '%s\n' "$HOME/.agi1/staging.env"
  fi
}

usage() {
  cat <<'USAGE'
Usage: ./scripts/validate_env.sh [--mode staging|production] [--env-file path] [--output path]

Runs environment and secret validation for AGI-1 launch prerequisites.

Options:
  --mode staging|production   Validation mode (default: staging)
  --env-file PATH             Source env file before validation
  --output PATH               Write JSON report (default: runtime/env_validation_report_<mode>.json)
  -h, --help                  Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
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

if [[ "$MODE" != "staging" && "$MODE" != "production" ]]; then
  echo "Invalid mode: $MODE" >&2
  exit 1
fi

if [[ -z "$ENV_FILE" ]]; then
  candidate="$(default_env_file)"
  if [[ -f "$candidate" ]]; then
    ENV_FILE="$candidate"
  fi
fi

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file not found: $ENV_FILE" >&2
    exit 1
  fi
  export AGI1_ENV_FILE="$ENV_FILE"
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$ROOT_DIR/runtime/env_validation_report_${MODE}.json"
fi
mkdir -p "$(dirname "$OUTPUT_PATH")"

PM_LINE="PM: OpenClaw"
EXEC_LINE="Exec: Jack | Julia | Singularity | Aegis"

echo "$PM_LINE"
echo "$EXEC_LINE"
echo "Running env validation (mode=$MODE)"

SECRET_EXIT=0
STACK_EXIT=0

if "$ROOT_DIR/scripts/print_required_secrets.sh" --mode "$MODE"; then
  SECRET_EXIT=0
else
  SECRET_EXIT=$?
fi

STACK_REPORT_PATH="$ROOT_DIR/runtime/env_check_${MODE}.json"
if (cd "$STACK_DIR" && PYTHONPATH=. python3 -m cli.env_check --mode "$MODE" > "$STACK_REPORT_PATH"); then
  STACK_EXIT=0
else
  STACK_EXIT=$?
fi

python3 - "$MODE" "$OUTPUT_PATH" "$STACK_REPORT_PATH" "$SECRET_EXIT" "$STACK_EXIT" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

mode = sys.argv[1]
output = pathlib.Path(sys.argv[2])
stack_report_path = pathlib.Path(sys.argv[3])
secret_exit = int(sys.argv[4])
stack_exit = int(sys.argv[5])

stack_payload = {}
if stack_report_path.exists():
    try:
        stack_payload = json.loads(stack_report_path.read_text(encoding="utf-8"))
    except Exception:
        stack_payload = {"ok": False, "error": "invalid_env_check_json"}
else:
    stack_payload = {"ok": False, "error": "missing_env_check_report"}

provider = str(__import__("os").environ.get("OPENCLAW_CALL_PROVIDER", "mock")).strip().lower()
provider_checks = {"provider": provider, "ok": True, "missing": []}
env = __import__("os").environ
if provider in {"livekit", "daily", "twilio"}:
    required = ["OPENCLAW_CALL_PROVIDER_API_KEY"]
    if provider in {"livekit", "twilio"}:
        required.append("OPENCLAW_CALL_PROVIDER_API_SECRET")
        required.append("OPENCLAW_CALL_PROVIDER_URL")
    if provider == "daily":
        required.append("OPENCLAW_CALL_PROVIDER_DOMAIN")
    missing = [key for key in required if not str(env.get(key, "")).strip()]
    provider_checks["missing"] = missing
    provider_checks["ok"] = len(missing) == 0

ok = secret_exit == 0 and stack_exit == 0 and bool(stack_payload.get("ok", False)) and provider_checks["ok"]
failure_reasons = []
if secret_exit != 0:
    failure_reasons.append("required_secrets_missing")
if stack_exit != 0 or not bool(stack_payload.get("ok", False)):
    failure_reasons.append("agi1_env_check_failed")
if not provider_checks["ok"]:
    failure_reasons.append("call_provider_env_missing")
payload = {
    "pm": "PM: OpenClaw",
    "exec": "Exec: Jack | Julia | Singularity | Aegis",
    "mode": mode,
    "env_file": str(__import__("os").environ.get("AGI1_ENV_FILE", "")) or "",
    "ok": ok,
    "checks": {
        "required_secrets": "PASS" if secret_exit == 0 else "FAIL",
        "agi1_env_check": "PASS" if stack_exit == 0 and bool(stack_payload.get("ok", False)) else "FAIL",
        "call_provider_env": "PASS" if provider_checks["ok"] else "FAIL",
    },
    "provider_checks": provider_checks,
    "env_check_report_path": str(stack_report_path),
    "env_check_report": stack_payload,
    "failure_reasons": failure_reasons,
    "computed_at": datetime.now(timezone.utc).isoformat(),
}
output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
sys.exit(0 if ok else 1)
PY
