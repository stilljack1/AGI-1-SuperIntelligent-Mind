#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE=""
REGION="${AWS_REGION:-us-east-2}"
SERVICE_CODE="ec2"
QUOTA_CODE="L-1216C47A"
REQUESTED_VALUE="64"
OUTPUT_PATH="$ROOT_DIR/runtime/aws_service_quota_request.json"
EXECUTE=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/request_aws_service_quota.sh [options]

Prepare or submit the AGI-1 EC2 standard on-demand vCPU quota request.

Options:
  --env-file PATH        Env file to source before running AWS CLI
  --region REGION        AWS region (default: AWS_REGION or us-east-2)
  --quota-code CODE      Service quota code (default: L-1216C47A)
  --requested-value N    Requested quota value (default: 64)
  --output PATH          JSON report output path
  --execute              Submit the request through AWS CLI
  -h, --help             Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --region)
      REGION="${2:-}"
      shift 2
      ;;
    --quota-code)
      QUOTA_CODE="${2:-}"
      shift 2
      ;;
    --requested-value)
      REQUESTED_VALUE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --execute)
      EXECUTE=1
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

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file not found: $ENV_FILE" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  REGION="${AWS_REGION:-$REGION}"
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

JUSTIFICATION="Scaling 1,000 concurrent AGI Supervisor agents for real-time WebRTC video orchestration and DynamoDB state synchronization."

python3 - "$OUTPUT_PATH" "$REGION" "$SERVICE_CODE" "$QUOTA_CODE" "$REQUESTED_VALUE" "$EXECUTE" "$JUSTIFICATION" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

output_path, region, service_code, quota_code, requested_value, execute, justification = sys.argv[1:]
payload = {
    "pm": "PM: OpenClaw",
    "exec": "Exec: Jack | Julia | Singularity | Aegis",
    "prepared_at": datetime.now(timezone.utc).isoformat(),
    "region": region,
    "service_code": service_code,
    "quota_code": quota_code,
    "requested_value": float(requested_value),
    "execute": execute == "1",
    "justification": justification,
    "status": "prepared",
    "notes": [
        "AWS documentation as of 2026-02-28 identifies L-1216C47A as the standard on-demand vCPU quota code for EC2.",
        "If the account uses a different internal quota mapping, override --quota-code explicitly."
    ],
}
path = pathlib.Path(output_path)
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

if [[ "$EXECUTE" -eq 0 ]]; then
  exit 0
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is not installed or not on PATH." >&2
  exit 127
fi

TMP_OUTPUT="$(mktemp)"
if aws service-quotas request-service-quota-increase \
  --region "$REGION" \
  --service-code "$SERVICE_CODE" \
  --quota-code "$QUOTA_CODE" \
  --desired-value "$REQUESTED_VALUE" \
  >"$TMP_OUTPUT" 2>&1; then
  python3 - "$OUTPUT_PATH" "$TMP_OUTPUT" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
tmp = pathlib.Path(sys.argv[2])
payload = json.loads(tmp.read_text(encoding="utf-8"))
payload["status"] = "submitted"
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY
else
  python3 - "$OUTPUT_PATH" "$TMP_OUTPUT" "$REGION" "$SERVICE_CODE" "$QUOTA_CODE" "$REQUESTED_VALUE" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

output_path, tmp_output, region, service_code, quota_code, requested_value = sys.argv[1:]
payload = {
    "pm": "PM: OpenClaw",
    "exec": "Exec: Jack | Julia | Singularity | Aegis",
    "prepared_at": datetime.now(timezone.utc).isoformat(),
    "region": region,
    "service_code": service_code,
    "quota_code": quota_code,
    "requested_value": float(requested_value),
    "execute": True,
    "status": "failed",
    "error": pathlib.Path(tmp_output).read_text(encoding="utf-8"),
}
path = pathlib.Path(output_path)
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
sys.exit(1)
PY
fi
