#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOBILE_DIR="$ROOT_DIR/apps/mobile"
GENERATED_FILE="$MOBILE_DIR/src/generated/buildEnv.ts"
PLATFORM=""
PROFILE="production"
ENV_FILE=""
PREPARE_ONLY=0
PASS_THROUGH=()

usage() {
  cat <<'USAGE'
Usage: ./scripts/mobile_eas_build.sh --platform ios|android [options] [-- extra eas args]

Loads AGI-1 mobile env values from a vault file, writes archive-safe build config,
and then runs `eas build`.

Options:
  --platform ios|android   Required build target
  --profile NAME          EAS build profile (default: production)
  --env-file PATH         Override env file (default: ~/.agi1/staging.env for non-production,
                          ~/.agi1/production.env for production)
  --prepare-only          Generate mobile build config and exit
  -h, --help              Show this help
USAGE
}

escape_ts_string() {
  local value="${1:-}"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  printf '%s' "$value"
}

default_env_file() {
  if [[ "$PROFILE" == "production" ]]; then
    printf '%s\n' "$HOME/.agi1/production.env"
  else
    printf '%s\n' "$HOME/.agi1/staging.env"
  fi
}

write_generated_env() {
  local api_url ws_url api_key call_provider source_label profile_label
  api_url="${EXPO_PUBLIC_API_URL:-http://localhost:8080}"
  ws_url="${EXPO_PUBLIC_WS_URL:-ws://localhost:8080}"
  api_key="${EXPO_PUBLIC_API_KEY:-}"
  call_provider="${EXPO_PUBLIC_CALL_PROVIDER:-mock}"
  source_label="${1:-shell}"
  profile_label="${2:-$PROFILE}"

  mkdir -p "$(dirname "$GENERATED_FILE")"

  cat > "$GENERATED_FILE" <<EOF
export type MobileBuildEnv = {
  apiUrl: string;
  wsUrl: string;
  apiKey: string;
  callProvider: string;
  buildProfile: string;
  source: string;
};

export const mobileBuildEnv: MobileBuildEnv = Object.freeze({
  apiUrl: "$(escape_ts_string "$api_url")",
  wsUrl: "$(escape_ts_string "$ws_url")",
  apiKey: "$(escape_ts_string "$api_key")",
  callProvider: "$(escape_ts_string "$call_provider")",
  buildProfile: "$(escape_ts_string "$profile_label")",
  source: "$(escape_ts_string "$source_label")",
});
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      PLATFORM="${2:-}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --prepare-only)
      PREPARE_ONLY=1
      shift
      ;;
    --)
      shift
      PASS_THROUGH=("$@")
      break
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

if [[ -z "$PLATFORM" ]]; then
  echo "--platform is required" >&2
  usage
  exit 1
fi

if [[ "$PLATFORM" != "ios" && "$PLATFORM" != "android" ]]; then
  echo "Invalid platform: $PLATFORM" >&2
  exit 1
fi

if [[ -z "$ENV_FILE" ]]; then
  ENV_FILE="$(default_env_file)"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Mobile env file not found: $ENV_FILE" >&2
  echo "Provide --env-file PATH or create the vault file before building." >&2
  exit 1
fi

MODE="staging"
if [[ "$PROFILE" == "production" ]]; then
  MODE="production"
fi

"$ROOT_DIR/scripts/validate_env.sh" --mode "$MODE" --env-file "$ENV_FILE" --output "$ROOT_DIR/runtime/env_validation_report_${MODE}_mobile.json"
"$ROOT_DIR/scripts/validate_mobile_build_env.sh" --env-file "$ENV_FILE" --profile "$PROFILE" --output "$ROOT_DIR/runtime/mobile_env_validation_${PROFILE}.json"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

export AGI1_ENV_FILE="$ENV_FILE"
export AGI1_MOBILE_PROFILE="$PROFILE"
export EXPO_PUBLIC_API_URL="${EXPO_PUBLIC_API_URL:-${PUBLIC_API_BASE_URL:-http://localhost:8080}}"
export EXPO_PUBLIC_WS_URL="${EXPO_PUBLIC_WS_URL:-${WS_BASE_URL:-ws://localhost:8080}}"
export EXPO_PUBLIC_API_KEY="${EXPO_PUBLIC_API_KEY:-${OPENCLAW_API_KEY:-}}"
export EXPO_PUBLIC_CALL_PROVIDER="${EXPO_PUBLIC_CALL_PROVIDER:-${OPENCLAW_CALL_PROVIDER:-mock}}"

write_generated_env "$ENV_FILE" "$PROFILE"

echo "Prepared mobile build env:"
echo "  platform: $PLATFORM"
echo "  profile: $PROFILE"
echo "  env file: $ENV_FILE"
echo "  api url: $EXPO_PUBLIC_API_URL"
echo "  ws url: $EXPO_PUBLIC_WS_URL"
echo "  call provider: $EXPO_PUBLIC_CALL_PROVIDER"

if [[ "$PREPARE_ONLY" -eq 1 ]]; then
  echo "Prepare only requested; skipping eas build."
  exit 0
fi

if ! command -v eas >/dev/null 2>&1; then
  echo "EAS CLI is not installed or not on PATH." >&2
  exit 127
fi

cd "$MOBILE_DIR"
exec eas build --platform "$PLATFORM" --profile "$PROFILE" "${PASS_THROUGH[@]}"
