#!/usr/bin/env bash
set -euo pipefail

OUTPUT="/Users/jatoine/Documents/agi1-avatar/agi1/reports/aws_preflight.json"
MODE="staging"

usage() {
  cat <<'USAGE'
Usage: ./scripts/aws_preflight.sh [--output PATH] [--mode staging|production]

Performs AWS preflight checks for STS, DynamoDB, and S3.
Outputs a JSON report with PASS/FAIL for each check.
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

if [[ "$MODE" != "staging" && "$MODE" != "production" ]]; then
  echo "Invalid mode: $MODE" >&2
  exit 1
fi

if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="/Users/jatoine/Documents/agi1-avatar/$OUTPUT"
fi
mkdir -p "$(dirname "$OUTPUT")"

AWS_REGION="${AWS_REGION:-}"
AGI1_STATE_TABLE="${AGI1_STATE_TABLE:-${ONE_MIND_DDB_TABLE:-}}"
AGI1_STATE_BUCKET="${AGI1_STATE_BUCKET:-${ONE_MIND_S3_BUCKET:-}}"
AGI1_STATE_PREFIX="${AGI1_STATE_PREFIX:-staging}"
AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-${LOCALSTACK_ENDPOINT_URL:-}}"

report_tmp="$(mktemp)"
trap 'rm -f "$report_tmp"' EXIT

python3 - "$MODE" "$OUTPUT" <<'PY'
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

mode = sys.argv[1]
output = pathlib.Path(sys.argv[2])

payload = {
    "pm": "PM: OpenClaw",
    "exec": "Exec: Jack | Julia | Singularity | Aegis",
    "mode": mode,
    "overall": "FAIL",
    "checks": [],
    "computed_at": datetime.now(timezone.utc).isoformat(),
}

required = {
    "AWS_REGION": os.getenv("AWS_REGION", "").strip(),
    "AGI1_STATE_TABLE": os.getenv("AGI1_STATE_TABLE", "").strip() or os.getenv("ONE_MIND_DDB_TABLE", "").strip(),
    "AGI1_STATE_BUCKET": os.getenv("AGI1_STATE_BUCKET", "").strip() or os.getenv("ONE_MIND_S3_BUCKET", "").strip(),
}
missing = [k for k, v in required.items() if not v]
if missing:
    payload["checks"].append(
        {
            "name": "required_env",
            "status": "FAIL",
            "details": {"missing": missing},
            "remediation": "Set missing AWS env keys and rerun.",
        }
    )
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    sys.exit(1)

output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

if [[ ! -x "$(command -v aws)" ]]; then
  python3 - "$OUTPUT" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["checks"].append(
    {"name": "aws_cli", "status": "FAIL", "details": {"error": "aws_cli_not_found"}, "remediation": "Install AWS CLI v2."}
)
payload["overall"] = "FAIL"
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY
  exit 1
fi

sts_status="FAIL"
sts_detail=""
if sts_json="$(aws sts get-caller-identity --output json 2>/dev/null)"; then
  sts_status="PASS"
  sts_detail="$sts_json"
else
  sts_status="FAIL"
  sts_detail="sts_identity_failed"
fi

ddb_status="FAIL"
ddb_detail=""
ddb_cmd=(aws dynamodb describe-table --table-name "$AGI1_STATE_TABLE" --region "$AWS_REGION" --output json)
if [[ -n "$AWS_ENDPOINT_URL" ]]; then
  ddb_cmd+=(--endpoint-url "$AWS_ENDPOINT_URL")
fi
if ddb_json="$("${ddb_cmd[@]}" 2>/dev/null)"; then
  ddb_status="PASS"
  ddb_detail="$ddb_json"
else
  ddb_status="FAIL"
  ddb_detail="describe_table_failed"
fi

s3_status="FAIL"
s3_detail=""
if aws s3api head-bucket --bucket "$AGI1_STATE_BUCKET" 2>/dev/null; then
  key="${AGI1_STATE_PREFIX%/}/preflight-$(date +%s).json"
  tmp_body="$(mktemp)"
  printf '{"source":"aws_preflight","ts":%s}\n' "$(date +%s)" > "$tmp_body"
  put_cmd=(aws s3api put-object --bucket "$AGI1_STATE_BUCKET" --key "$key" --body "$tmp_body")
  head_cmd=(aws s3api head-object --bucket "$AGI1_STATE_BUCKET" --key "$key")
  if [[ -n "$AWS_ENDPOINT_URL" ]]; then
    put_cmd+=(--endpoint-url "$AWS_ENDPOINT_URL")
    head_cmd+=(--endpoint-url "$AWS_ENDPOINT_URL")
  fi
  if "${put_cmd[@]}" >/dev/null 2>&1 && "${head_cmd[@]}" >/dev/null 2>&1; then
    s3_status="PASS"
    s3_detail="$key"
  else
    s3_status="FAIL"
    s3_detail="s3_write_or_head_failed"
  fi
  rm -f "$tmp_body"
else
  s3_status="FAIL"
  s3_detail="head_bucket_failed"
fi

python3 - "$OUTPUT" "$sts_status" "$sts_detail" "$ddb_status" "$ddb_detail" "$s3_status" "$s3_detail" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
sts_status, sts_detail = sys.argv[2], sys.argv[3]
ddb_status, ddb_detail = sys.argv[4], sys.argv[5]
s3_status, s3_detail = sys.argv[6], sys.argv[7]

payload = json.loads(path.read_text(encoding="utf-8"))
payload["checks"].append(
    {"name": "sts_identity", "status": sts_status, "details": {"result": sts_detail if sts_status == "PASS" else "", "error": sts_detail if sts_status != "PASS" else ""}}
)
payload["checks"].append(
    {"name": "dynamodb_table", "status": ddb_status, "details": {"result": ddb_detail if ddb_status == "PASS" else "", "error": ddb_detail if ddb_status != "PASS" else ""}}
)
payload["checks"].append(
    {"name": "s3_bucket_rw", "status": s3_status, "details": {"key": s3_detail if s3_status == "PASS" else "", "error": s3_detail if s3_status != "PASS" else ""}}
)
payload["overall"] = "PASS" if all(c["status"] == "PASS" for c in payload["checks"]) else "FAIL"
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
sys.exit(0 if payload["overall"] == "PASS" else 1)
PY
