#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8080}"

pretty_json() {
  python3 -m json.tool
}

echo "[1] health"
curl -fsS "$API_URL/healthz" | pretty_json

echo "[2] create session"
SESSION_JSON=$(curl -fsS -X POST "$API_URL/v1/sessions" \
  -H 'content-type: application/json' \
  -d '{"user_id":"smoke-user","input_lang":"auto","output_lang":"en","auto_detect":true}')

echo "$SESSION_JSON" | pretty_json

SESSION_ID=$(echo "$SESSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["session_id"])')
TOKEN=$(echo "$SESSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')

echo "[3] execute task"
curl -fsS -X POST "$API_URL/v1/task/execute" \
  -H 'content-type: application/json' \
  -d "{\"session_id\":\"$SESSION_ID\",\"token\":\"$TOKEN\",\"task\":\"Run smoke task\",\"style_preset\":\"trust\",\"whisper_mode\":false}" | pretty_json

echo "Smoke test finished."
