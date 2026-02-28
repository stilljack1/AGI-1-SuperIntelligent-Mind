#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK_DIR="$ROOT_DIR/agi1"
MODE="staging"
DO_PROVISION=0
DO_DEPLOY=0
DO_SMOKE=0
DO_LOAD=0
DO_DRILL=0
DO_PROMOTE=0
DO_VALIDATE=1

usage() {
  cat <<'USAGE'
Usage: ./scripts/launch_activate.sh [options]

Options:
  --mode staging|production   Target mode (default: staging)
  --provision                 Create/check state resources (requires AWS env vars)
  --deploy                    Build UI and validate API package imports
  --smoke                     Run staging smoke and write runtime/final_smoke_report.json
  --load                      Run load test and write runtime/load_report.json
  --drill                     Run kill-switch drill and write runtime/drill_report.json
  --promote                   Attempt manifest promotion apply if all gates pass
  --no-validate               Skip preflight env validation (not recommended)
  -h, --help                  Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --provision)
      DO_PROVISION=1
      shift
      ;;
    --deploy)
      DO_DEPLOY=1
      shift
      ;;
    --smoke)
      DO_SMOKE=1
      shift
      ;;
    --load)
      DO_LOAD=1
      shift
      ;;
    --drill)
      DO_DRILL=1
      shift
      ;;
    --promote)
      DO_PROMOTE=1
      shift
      ;;
    --no-validate)
      DO_VALIDATE=0
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

if [[ ! -d "$STACK_DIR" ]]; then
  echo "Missing required directory: $STACK_DIR" >&2
  exit 1
fi

EVIDENCE_DIR="$STACK_DIR/runtime"
mkdir -p "$EVIDENCE_DIR"

echo "PM: OpenClaw"
echo "Exec: Jack | Julia | Singularity | Aegis"
echo "LAUNCH_ACTIVATE start (mode=$MODE)"

if [[ "$DO_VALIDATE" -eq 1 ]]; then
  echo "[preflight] Validating environment and required secrets..."
  "$ROOT_DIR/scripts/validate_env.sh" \
    --mode "$MODE" \
    --output "$ROOT_DIR/runtime/env_validation_report_${MODE}.json"
fi

if [[ "$DO_DEPLOY" -eq 1 ]]; then
  echo "[deploy] Building web UI..."
  (cd "$ROOT_DIR/apps/ui" && npm run build)
  echo "[deploy] Verifying API imports..."
  (
    cd "$ROOT_DIR/apps/api"
    PYTHONPATH=../../packages/core/src:../../packages/memory/voice_profiles/src:../../packages \
      python3 -m py_compile app/main.py app/api/routes.py app/core/task_runtime.py app/ws/tasks.py
  )
fi

if [[ "$DO_PROVISION" -eq 1 ]]; then
  : "${AWS_REGION:?AWS_REGION is required for --provision}"
  : "${AGI1_STATE_TABLE:?AGI1_STATE_TABLE is required for --provision}"
  : "${AGI1_STATE_BUCKET:?AGI1_STATE_BUCKET is required for --provision}"
  : "${AGI1_STATE_PREFIX:?AGI1_STATE_PREFIX is required for --provision}"

  echo "[provision] Checking/creating staging state resources..."
  (
    cd "$STACK_DIR"
    PYTHONPATH=. python3 -m cli.provision_state_resources \
      --mode "$MODE" \
      --region "$AWS_REGION" \
      --table-name "$AGI1_STATE_TABLE" \
      --bucket-name "$AGI1_STATE_BUCKET" \
      --prefix "$AGI1_STATE_PREFIX" \
      --output runtime/provision_report.json
  )
fi

if [[ "$DO_SMOKE" -eq 1 ]]; then
  echo "[smoke] Running staging smoke..."
  (cd "$STACK_DIR" && PYTHONPATH=. python3 scripts/e2e_staging_smoke.py --output runtime/final_smoke_report.json)
  (cd "$STACK_DIR" && cp runtime/final_smoke_report.json runtime/staging_smoke_report.json)
  echo "[smoke] Verifying sovereign handshake enforcement..."
  (
    cd "$ROOT_DIR"
    PYTHONPATH=apps/api:packages/core/src:packages/memory/voice_profiles/src:packages \
      python3 scripts/handshake_smoke.py --output agi1/runtime/handshake_smoke_report.json
  )
fi

if [[ "$DO_LOAD" -eq 1 ]]; then
  echo "[load] Running load test..."
  (cd "$STACK_DIR" && PYTHONPATH=. python3 scripts/load_test_99.py --mode "$MODE" --output runtime/load_report.json)
fi

if [[ "$DO_DRILL" -eq 1 ]]; then
  echo "[drill] Running kill-switch drill..."
  (cd "$STACK_DIR" && ./scripts/kill_switch_drill.sh --output runtime/drill_report.json)
fi

RELEASE_EXIT=0
READINESS_EXIT=0

if [[ "$DO_SMOKE" -eq 1 || "$DO_LOAD" -eq 1 || "$DO_DRILL" -eq 1 ]]; then
  echo "[capabilities] Verifying capability evidence..."
  (
    cd "$STACK_DIR"
    PYTHONPATH=. python3 -m cli.verify_capabilities \
      --mode "$MODE" \
      --out runtime/capability_evidence.json \
      --report reports/capability_verification_${MODE}.md
  )

  echo "[gates] Evaluating release gates from evidence..."
  (
    cd "$STACK_DIR"
    PYTHONPATH=. python3 -m cli.release_gate_eval --mode "$MODE" --evidence-dir runtime/ --output runtime/release_gates_status.json
  ) || RELEASE_EXIT=$?

  echo "[gates] Running strict manifest readiness..."
  (
    cd "$STACK_DIR"
    PYTHONPATH=. python3 -m cli.manifest_readiness --strict --mode "$MODE" > runtime/manifest_readiness_strict.json
  ) || READINESS_EXIT=$?
fi

if [[ "$DO_PROMOTE" -eq 1 ]]; then
  if [[ "$RELEASE_EXIT" -ne 0 || "$READINESS_EXIT" -ne 0 ]]; then
    echo "Promotion blocked: release gates/readiness not green." >&2
    exit 1
  fi
  echo "[promote] Applying manifest promotion..."
  (
    cd "$STACK_DIR"
    PYTHONPATH=. python3 -m cli.promote_manifests \
      --mode "$MODE" \
      --capability-evidence runtime/capability_evidence.json \
      --output runtime/manifest_promotion_report.json \
      --apply > runtime/promotion_apply.json
  )
fi

echo "LAUNCH_ACTIVATE complete. Evidence:"
echo "  - $EVIDENCE_DIR/final_smoke_report.json"
echo "  - $EVIDENCE_DIR/staging_smoke_report.json"
echo "  - $EVIDENCE_DIR/handshake_smoke_report.json"
echo "  - $EVIDENCE_DIR/load_report.json"
echo "  - $EVIDENCE_DIR/drill_report.json"
echo "  - $EVIDENCE_DIR/release_gates_status.json"
echo "  - $EVIDENCE_DIR/capability_evidence.json"
echo "  - $EVIDENCE_DIR/manifest_promotion_report.json"
echo "  - $EVIDENCE_DIR/manifest_readiness_strict.json"
echo "  - $ROOT_DIR/runtime/env_validation_report_${MODE}.json"

if [[ "$RELEASE_EXIT" -ne 0 || "$READINESS_EXIT" -ne 0 ]]; then
  exit 1
fi
