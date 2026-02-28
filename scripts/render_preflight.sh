#!/usr/bin/env bash
set -euo pipefail

OUTPUT="/Users/jatoine/Documents/agi1-avatar/agi1/reports/render_preflight.json"
MODE="staging"

usage() {
  cat <<'USAGE'
Usage: ./scripts/render_preflight.sh [--output PATH] [--mode staging|production]

Validates Render API connectivity with masked-key handling.
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

RENDER_API_KEY="${RENDER_API_KEY:-}"
RENDER_API_BASE="${RENDER_API_BASE:-https://api.render.com/v1/services?limit=1}"

if [[ -z "$RENDER_API_KEY" ]]; then
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
      "details": {"missing": ["RENDER_API_KEY"]},
      "remediation": "Set RENDER_API_KEY and rerun."
    }
  ]
}
EOF
  cat "$OUTPUT"
  exit 1
fi

status_code="$(curl -sS -o /tmp/render_preflight_body.json -w "%{http_code}" \
  -X GET "$RENDER_API_BASE" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Accept: application/json" || true)"

overall="FAIL"
check_status="FAIL"
error_code=""
summary=""
if [[ "$status_code" =~ ^2 ]]; then
  overall="PASS"
  check_status="PASS"
  summary="$(python3 - <<'PY'
import json, pathlib
path = pathlib.Path("/tmp/render_preflight_body.json")
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("ok_non_json")
    raise SystemExit(0)
if isinstance(payload, list):
    print(f"services_count={len(payload)}")
elif isinstance(payload, dict):
    print("dict_payload")
else:
    print("unknown_payload")
PY
)"
else
  error_code="http_error"
  summary="status_${status_code:-unknown}"
fi

cat > "$OUTPUT" <<EOF
{
  "pm": "PM: OpenClaw",
  "exec": "Exec: Jack | Julia | Singularity | Aegis",
  "mode": "$MODE",
  "overall": "$overall",
  "checks": [
    {
      "name": "render_api",
      "status": "$check_status",
      "details": {
        "endpoint": "$RENDER_API_BASE",
        "http_status": "$status_code",
        "error_code": "$error_code",
        "summary": "$summary"
      },
      "remediation": "Verify Render API key, endpoint, and network egress."
    }
  ]
}
EOF

cat "$OUTPUT"
[[ "$overall" == "PASS" ]]
