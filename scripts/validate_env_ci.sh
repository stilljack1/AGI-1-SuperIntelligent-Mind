#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-staging}"

if [[ "$MODE" != "staging" && "$MODE" != "production" ]]; then
  echo "Mode must be staging or production" >&2
  exit 1
fi

required_keys=(
  AWS_REGION
  AGI1_STATE_TABLE
  AGI1_STATE_BUCKET
  AGI1_STATE_PREFIX
  ONE_MIND_TOKEN_SECRET
  ONE_MIND_HANDSHAKE_SECRET
  OPENCLAW_CALL_PROVIDER
  PUBLIC_API_BASE_URL
  WS_BASE_URL
  WAR_ROOM_API_KEY
  WAR_ROOM_WEBHOOK_SECRET
)

if [[ "$MODE" == "staging" ]]; then
  required_keys+=(RAILWAY_API_KEY RENDER_API_KEY)
fi

missing=0
for key in "${required_keys[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    echo "MISSING: $key"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

echo "All required CI env keys are present for mode=$MODE"
