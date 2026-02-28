#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${AGI1_STAGING_ENV_FILE:-$HOME/.agi1/staging.env}"

usage() {
  cat <<'USAGE'
Usage: ./scripts/load_env_staging.sh [--env-file PATH]

Loads staging secrets from a local vault file outside git.

Defaults:
  ENV file: ~/.agi1/staging.env

Options:
  --env-file PATH   Override path to staging env file
  -h, --help        Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
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

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Staging env file not found: $ENV_FILE" >&2
  echo "Create it outside git with chmod 600." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required=(
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
  RAILWAY_API_KEY
  RENDER_API_KEY
)

echo "PM: OpenClaw"
echo "Exec: Jack | Julia | Singularity | Aegis"
echo "Loaded staging env file: $ENV_FILE"
echo "Loaded keys (names only):"

missing=()
for key in "${required[@]}"; do
  if [[ -n "${!key:-}" ]]; then
    echo "  - $key (SET)"
  else
    echo "  - $key (MISSING)"
    missing+=("$key")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Missing required keys after load: ${missing[*]}" >&2
  exit 1
fi

echo "Staging environment loaded successfully."
