#!/usr/bin/env bash
set -euo pipefail

PM_LABEL="OpenClaw"
EXEC_LABEL="Agent 1 Jack | Agent 2 Julia | Agent 3 Singularity | Agent 4 Aegis"

REGION="${AWS_REGION:-us-east-1}"
TABLE="${AGI1_DYNAMODB_TABLE:-agi1_state_store}"
BUCKET="${AGI1_S3_BUCKET:-agi1-artifacts}"
DRY_RUN="${DRY_RUN:-1}"

SESSION_ID="restore-drill-$(date +%s)"
TIMESTAMP="$(date +%s)"
OBJECT_KEY="logs/restore-drill/${SESSION_ID}.json"
TMP_FILE="/tmp/${SESSION_ID}.json"
RESTORED_FILE="/tmp/${SESSION_ID}.restored.json"

cat > "${TMP_FILE}" <<EOF
{"pm":"${PM_LABEL}","exec":"${EXEC_LABEL}","session_id":"${SESSION_ID}","timestamp":${TIMESTAMP},"status":"drill"}
EOF

echo "PM: ${PM_LABEL}"
echo "Exec: ${EXEC_LABEL}"
echo "Region: ${REGION}"
echo "DynamoDB table: ${TABLE}"
echo "S3 bucket: ${BUCKET}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "[DRY_RUN] Would execute:"
  echo "  aws dynamodb put-item --table-name ${TABLE} --region ${REGION} --item ..."
  echo "  aws dynamodb get-item --table-name ${TABLE} --region ${REGION} --key ..."
  echo "  aws s3api put-object --bucket ${BUCKET} --key ${OBJECT_KEY} --body ${TMP_FILE}"
  echo "  aws s3api list-object-versions --bucket ${BUCKET} --prefix ${OBJECT_KEY}"
  echo "  aws s3api get-object --bucket ${BUCKET} --key ${OBJECT_KEY} --version-id <VERSION_ID> ${RESTORED_FILE}"
  echo "[DRY_RUN] Restore drill command plan complete."
  exit 0
fi

aws dynamodb put-item \
  --region "${REGION}" \
  --table-name "${TABLE}" \
  --item "{
    \"session_id\": {\"S\": \"${SESSION_ID}\"},
    \"timestamp\": {\"N\": \"${TIMESTAMP}\"},
    \"status\": {\"S\": \"restore_drill\"},
    \"payload\": {\"S\": \"$(cat "${TMP_FILE}" | tr -d '\n' | sed 's/"/\\"/g')\"}
  }" >/dev/null

aws dynamodb get-item \
  --region "${REGION}" \
  --table-name "${TABLE}" \
  --key "{
    \"session_id\": {\"S\": \"${SESSION_ID}\"},
    \"timestamp\": {\"N\": \"${TIMESTAMP}\"}
  }" >/dev/null

aws s3api put-object \
  --region "${REGION}" \
  --bucket "${BUCKET}" \
  --key "${OBJECT_KEY}" \
  --body "${TMP_FILE}" >/dev/null

VERSION_ID="$(aws s3api list-object-versions \
  --region "${REGION}" \
  --bucket "${BUCKET}" \
  --prefix "${OBJECT_KEY}" \
  --query 'Versions[0].VersionId' \
  --output text)"

if [[ -z "${VERSION_ID}" || "${VERSION_ID}" == "None" ]]; then
  echo "Restore drill failed: no S3 version ID returned."
  exit 1
fi

aws s3api get-object \
  --region "${REGION}" \
  --bucket "${BUCKET}" \
  --key "${OBJECT_KEY}" \
  --version-id "${VERSION_ID}" \
  "${RESTORED_FILE}" >/dev/null

if [[ ! -s "${RESTORED_FILE}" ]]; then
  echo "Restore drill failed: restored file is empty."
  exit 1
fi

echo "Restore drill passed."
echo "Restored object path: ${RESTORED_FILE}"
