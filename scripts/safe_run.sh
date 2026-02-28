#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/safe_run.sh <script_path> [args...]" >&2
  exit 1
fi

TARGET="$1"
shift || true

if [[ ! -f "$TARGET" ]]; then
  echo "safe_run: script not found: $TARGET" >&2
  exit 1
fi

# Always execute scripts via bash to avoid zsh history/glob parsing issues.
exec /bin/bash "$TARGET" "$@"
