#!/usr/bin/env bash
set -euo pipefail

OUTPUT="/Users/jatoine/Documents/agi1-avatar/agi1/reports/railway_preflight.json"
MODE="staging"

usage() {
  cat <<'USAGE'
Usage: ./scripts/railway_preflight.sh [--output PATH] [--mode staging|production]

Validates Railway API connectivity with masked-key handling.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
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

if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="/Users/jatoine/Documents/agi1-avatar/$OUTPUT"
fi
mkdir -p "$(dirname "$OUTPUT")"

RAILWAY_API_KEY="${RAILWAY_API_KEY:-}"
RAILWAY_API_BASE="${RAILWAY_API_BASE:-https://backboard.railway.app/graphql/v2}"

if [[ -z "$RAILWAY_API_KEY" ]]; then
  cat > "$OUTPUT" <<EOF
{
  "pm": "PM: OpenClaw",
  "exec": "Exec: Jack | Julia | Singularity | Aegis",
  "mode": "$MODE",
  "overall": "FAIL",
  "checks": [
    {
      "name": "required_env",
      "status": "FAIL",
      "details": {"missing": ["RAILWAY_API_KEY"]},
      "remediation": "Set RAILWAY_API_KEY and rerun."
    }
  ]
}
EOF
  cat "$OUTPUT"
  exit 1
fi

status_code="$(curl -sS -o /tmp/railway_preflight_body.json -w "%{http_code}" \
  -X POST "$RAILWAY_API_BASE" \
  -H "Authorization: Bearer $RAILWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ me { id email } }"}' || true)"

overall="FAIL"
check_status="FAIL"
error_code=""
errors=""
if [[ "$status_code" =~ ^2 ]]; then
  if python3 - <<'PY'
import json
import pathlib
import sys
path = pathlib.Path("/tmp/railway_preflight_body.json")
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    sys.exit(2)
if payload.get("errors"):
    sys.exit(1)
sys.exit(0)
PY
  then
    overall="PASS"
    check_status="PASS"
  else
    error_code="graphql_error"
    errors="$(python3 - <<'PY'
import json, pathlib
path = pathlib.Path("/tmp/railway_preflight_body.json")
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(payload.get("errors", [])))
except Exception:
    print("invalid_json")
PY
)"
  fi
else
  error_code="http_error"
  errors="status_${status_code:-unknown}"
fi

cat > "$OUTPUT" <<EOF
{
  "pm": "PM: OpenClaw",
  "exec": "Exec: Jack | Julia | Singularity | Aegis",
  "mode": "$MODE",
  "overall": "$overall",
  "checks": [
    {
      "name": "railway_api",
      "status": "$check_status",
      "details": {
        "endpoint": "$RAILWAY_API_BASE",
        "http_status": "$status_code",
        "error_code": "$error_code",
        "errors": "$errors"
      },
      "remediation": "Verify Railway API key, endpoint, and network egress."
    }
  ]
}
EOF

cat "$OUTPUT"
[[ "$overall" == "PASS" ]]
