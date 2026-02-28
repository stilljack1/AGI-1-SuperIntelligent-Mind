#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=""
PROFILE="production"
OUTPUT_PATH=""

usage() {
  cat <<'USAGE'
Usage: ./scripts/validate_mobile_build_env.sh --env-file PATH [--profile NAME] [--output PATH]

Validate the mobile archive environment mapping before running EAS.
The env file must provide keys that map deterministically into:
  EXPO_PUBLIC_API_URL
  EXPO_PUBLIC_WS_URL
  EXPO_PUBLIC_API_KEY
  EXPO_PUBLIC_CALL_PROVIDER
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
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

if [[ -z "$ENV_FILE" ]]; then
  echo "--env-file is required" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Mobile env file not found: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required=(
  "PUBLIC_API_BASE_URL"
  "WS_BASE_URL"
  "OPENCLAW_CALL_PROVIDER"
)

if [[ "$PROFILE" == "production" ]]; then
  required+=(
    "ONE_MIND_TOKEN_SECRET"
    "ONE_MIND_HANDSHAKE_SECRET"
  )
fi

missing=()
for key in "${required[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    missing+=("$key")
  fi
done

mapped_api="${EXPO_PUBLIC_API_URL:-${PUBLIC_API_BASE_URL:-}}"
mapped_ws="${EXPO_PUBLIC_WS_URL:-${WS_BASE_URL:-}}"
mapped_key="${EXPO_PUBLIC_API_KEY:-${OPENCLAW_API_KEY:-}}"
mapped_provider="${EXPO_PUBLIC_CALL_PROVIDER:-${OPENCLAW_CALL_PROVIDER:-}}"

if [[ -z "$mapped_api" ]]; then
  missing+=("EXPO_PUBLIC_API_URL")
fi
if [[ -z "$mapped_ws" ]]; then
  missing+=("EXPO_PUBLIC_WS_URL")
fi
if [[ -z "$mapped_provider" ]]; then
  missing+=("EXPO_PUBLIC_CALL_PROVIDER")
fi

python3 - "$ENV_FILE" "$PROFILE" "${OUTPUT_PATH:-}" "${mapped_api:-}" "${mapped_ws:-}" "${mapped_provider:-}" "${mapped_key:-}" "${missing[*]:-}" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

env_file, profile, output_path, api_url, ws_url, provider, api_key, missing_joined = sys.argv[1:]
missing = [item for item in missing_joined.split() if item]
payload = {
    "pm": "PM: OpenClaw",
    "exec": "Exec: Jack | Julia | Singularity | Aegis",
    "env_file": env_file,
    "profile": profile,
    "ok": len(missing) == 0,
    "mapped": {
        "EXPO_PUBLIC_API_URL": api_url,
        "EXPO_PUBLIC_WS_URL": ws_url,
        "EXPO_PUBLIC_CALL_PROVIDER": provider,
        "EXPO_PUBLIC_API_KEY": "(SET)" if api_key else "(EMPTY)",
    },
    "missing": missing,
    "computed_at": datetime.now(timezone.utc).isoformat(),
}
if output_path:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
sys.exit(0 if payload["ok"] else 1)
PY
