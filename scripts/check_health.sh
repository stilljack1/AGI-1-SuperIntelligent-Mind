#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# api local ports (try common ones)
for p in 8000 3000 5000; do
  if curl -sS -f "http://127.0.0.1:${p}/health" >/dev/null 2>&1; then
    echo "OK: health on port ${p}"
    curl -s "http://127.0.0.1:${p}/health"
    exit 0
  fi
done
echo "ERR: no local health endpoint found on ports 8000/3000/5000"
exit 2
