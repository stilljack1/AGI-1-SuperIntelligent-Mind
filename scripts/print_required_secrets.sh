#!/usr/bin/env bash
set -euo pipefail

MODE="staging"
SHOW_VALUES=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/print_required_secrets.sh [--mode staging|production] [--show-values]

Print required launch secrets and fail when any required values are missing.

Options:
  --mode staging|production   Validation mode (default: staging)
  --show-values               Print masked values for configured keys
  -h, --help                  Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --show-values)
      SHOW_VALUES=1
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

if [[ "$MODE" != "staging" && "$MODE" != "production" ]]; then
  echo "Invalid mode: $MODE" >&2
  exit 1
fi

required_common=(
  "AWS_REGION:AWS_REGION"
  "AGI1_STATE_TABLE:AGI1_STATE_TABLE,ONE_MIND_DDB_TABLE"
  "AGI1_STATE_BUCKET:AGI1_STATE_BUCKET,ONE_MIND_S3_BUCKET"
  "AGI1_STATE_PREFIX:AGI1_STATE_PREFIX"
  "ONE_MIND_TOKEN_SECRET:ONE_MIND_TOKEN_SECRET"
  "ONE_MIND_HANDSHAKE_SECRET:ONE_MIND_HANDSHAKE_SECRET"
  "OPENCLAW_CALL_PROVIDER:OPENCLAW_CALL_PROVIDER"
  "PUBLIC_API_BASE_URL:PUBLIC_API_BASE_URL"
  "WS_BASE_URL:WS_BASE_URL"
  "WAR_ROOM_API_KEY:WAR_ROOM_API_KEY"
  "WAR_ROOM_WEBHOOK_SECRET:WAR_ROOM_WEBHOOK_SECRET"
)

required_staging=(
  "RAILWAY_API_KEY:RAILWAY_API_KEY"
  "RENDER_API_KEY:RENDER_API_KEY"
)

required_production=()

provider="${OPENCLAW_CALL_PROVIDER:-mock}"
provider_specific=()
case "$provider" in
  livekit)
    provider_specific+=(
      "OPENCLAW_CALL_PROVIDER_API_KEY:OPENCLAW_CALL_PROVIDER_API_KEY"
      "OPENCLAW_CALL_PROVIDER_API_SECRET:OPENCLAW_CALL_PROVIDER_API_SECRET"
      "OPENCLAW_CALL_PROVIDER_URL:OPENCLAW_CALL_PROVIDER_URL"
    )
    ;;
  daily)
    provider_specific+=(
      "OPENCLAW_CALL_PROVIDER_API_KEY:OPENCLAW_CALL_PROVIDER_API_KEY"
      "OPENCLAW_CALL_PROVIDER_DOMAIN:OPENCLAW_CALL_PROVIDER_DOMAIN"
    )
    ;;
  twilio)
    provider_specific+=(
      "OPENCLAW_CALL_PROVIDER_API_KEY:OPENCLAW_CALL_PROVIDER_API_KEY"
      "OPENCLAW_CALL_PROVIDER_API_SECRET:OPENCLAW_CALL_PROVIDER_API_SECRET"
      "OPENCLAW_CALL_PROVIDER_URL:OPENCLAW_CALL_PROVIDER_URL"
    )
    ;;
  mock)
    ;;
  *)
    provider_specific+=(
      "OPENCLAW_CALL_PROVIDER_API_KEY:OPENCLAW_CALL_PROVIDER_API_KEY"
      "OPENCLAW_CALL_PROVIDER_API_SECRET:OPENCLAW_CALL_PROVIDER_API_SECRET"
    )
    ;;
esac

required=("${required_common[@]}")
if [[ "$MODE" == "staging" ]]; then
  required+=("${required_staging[@]}")
else
  required+=("${required_production[@]}")
fi
if [[ ${#provider_specific[@]} -gt 0 ]]; then
  required+=("${provider_specific[@]}")
fi

mask_value() {
  local value="$1"
  local length=${#value}
  if [[ $length -le 6 ]]; then
    printf '%*s' "$length" '' | tr ' ' '*'
    return
  fi
  printf "%s***%s" "${value:0:3}" "${value:length-2:2}"
}

echo "PM: OpenClaw"
echo "Exec: Jack | Julia | Singularity | Aegis"
echo "Mode: $MODE"
echo "Call Provider: $provider"
echo "Required Secrets:"

missing=()
for spec in "${required[@]}"; do
  key="${spec%%:*}"
  aliases_csv="${spec#*:}"
  IFS=',' read -r -a aliases <<< "$aliases_csv"
  value=""
  for alias in "${aliases[@]}"; do
    alias_value="${!alias:-}"
    if [[ -n "$alias_value" ]]; then
      value="$alias_value"
      break
    fi
  done
  if [[ -z "$value" ]]; then
    missing+=("$key")
    echo "  - $key (MISSING)"
  else
    if [[ "$SHOW_VALUES" -eq 1 ]]; then
      echo "  - $key=$(mask_value "$value")"
    else
      echo "  - $key (SET)"
    fi
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo
  echo "Missing required secrets (${#missing[@]}):"
  for key in "${missing[@]}"; do
    echo "  - $key"
  done
  exit 1
fi

echo
echo "All required secrets are present."
