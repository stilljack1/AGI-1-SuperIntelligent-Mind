#!/bin/bash
# AGI-1 Sovereign Execution Engine (local deterministic harness)
# PM: OpenClaw
# Exec: Jack | Julia | Singularity | Aegis

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INTENT="${1:-Default mission}"
RISK_SCORE="${2:-0.5}"
MODEL_A="${3:-0.995}"
MODEL_B="${4:-0.992}"
MODEL_C="${5:-0.994}"
HIGH_STAKES="${6:-false}"

echo "PM: OpenClaw"
echo "Exec: Jack | Julia | Singularity | Aegis"
echo "Running sovereign execution check..."

python3 - <<'PY' "$INTENT" "$RISK_SCORE" "$MODEL_A" "$MODEL_B" "$MODEL_C" "$HIGH_STAKES"
import json
import sys

from singularity_prime.sovereign.engine import SovereignEngine

intent = sys.argv[1]
risk_score = float(sys.argv[2])
model_outputs = [float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])]
high_stakes = sys.argv[6].lower() in {"1", "true", "yes", "on"}

engine = SovereignEngine()
decision = engine.run(
    intent=intent,
    risk_score=risk_score,
    model_outputs=model_outputs,
    high_stakes=high_stakes,
)

payload = {
    "mode": decision.plan.mode,
    "intent": decision.plan.intent,
    "risk_score": decision.plan.risk_score,
    "lqm_status": decision.lqm_status,
    "lam_ready": decision.lam_ready,
    "consensus_weighted_score": round(decision.consensus.weighted_score, 6),
    "consensus_threshold": decision.consensus.threshold,
    "reasons": list(decision.consensus.reasons),
    "stages": list(decision.plan.stages),
}
print(json.dumps(payload, indent=2))
PY
