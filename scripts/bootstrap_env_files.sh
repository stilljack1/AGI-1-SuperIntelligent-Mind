#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${HOME}/.agi1"

mkdir -p "$TARGET_DIR"

for name in staging production; do
  target_file="$TARGET_DIR/${name}.env"
  template_file="$ROOT_DIR/env_templates/${name}.env.template"
  if [[ ! -f "$target_file" ]]; then
    cp "$template_file" "$target_file"
    chmod 600 "$target_file"
    echo "Created $target_file from template."
  else
    echo "Skipped existing $target_file."
  fi
done
