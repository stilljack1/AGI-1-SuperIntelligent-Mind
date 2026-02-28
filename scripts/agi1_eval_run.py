#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agi1_eval.engine import EvalEngine  # noqa: E402


def _build_suite() -> List[Dict[str, Any]]:
    base_time = datetime.now(timezone.utc)
    return [
        {
            "plan": {"goal": "Generate deterministic summary", "domain": "deterministic", "steps": ["summarize"]},
            "artifacts": {
                "output_text": "Summary generated successfully.",
                "tests_passed": True,
                "invariants_ok": True,
                "latency_p95_ms": 320,
            },
            "context": {
                "risk_level": "low",
                "verifiable": True,
                "nonce": "suite-1",
                "timestamp": base_time.isoformat(),
                "webhook_required": False,
            },
        },
        {
            "plan": {"goal": "Analyze strategy and produce answer", "domain": "reasoning", "steps": ["analyze"]},
            "artifacts": {
                "output_text": "Analysis complete.",
                "tests_passed": True,
                "invariants_ok": True,
                "latency_p95_ms": 780,
            },
            "context": {
                "risk_level": "medium",
                "verifiable": True,
                "nonce": "suite-2",
                "timestamp": (base_time + timedelta(seconds=5)).isoformat(),
                "webhook_required": False,
            },
        },
        {
            "plan": {"goal": "Attempt unknown operation", "domain": "code_generation", "steps": ["code"]},
            "artifacts": {
                "output_text": "Potentially unverifiable response",
                "latency_p95_ms": 250,
            },
            "context": {
                "risk_level": "medium",
                "verifiable": False,
                "nonce": "suite-3",
                "timestamp": (base_time + timedelta(seconds=10)).isoformat(),
                "webhook_required": False,
            },
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AGI-1 99.99% evaluation enforcement suite")
    parser.add_argument("--window", type=int, default=10000)
    parser.add_argument("--confidence", type=float, default=0.99)
    parser.add_argument("--threshold", type=float, default=0.9999)
    parser.add_argument("--domain", default="all")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if certification misses threshold")
    args = parser.parse_args()

    os.environ.setdefault("AGI1_STORE_MODE", "local")
    engine = EvalEngine.from_env()

    decisions = []
    for case in _build_suite():
        decision = engine.evaluate(case["plan"], case["artifacts"], case["context"], policy=None)
        engine.record(decision)
        decisions.append(decision)

    report = engine.certify(
        window=args.window,
        domain=args.domain,
        threshold_p=args.threshold,
        confidence=args.confidence,
    )

    print("PM: OpenClaw")
    print("Exec: Jack | Julia | Singularity | Aegis")
    print("Evaluation decisions:")
    for decision in decisions:
        print(
            f"- id={decision.decision_id} domain={decision.domain} action={decision.action.value} "
            f"score={decision.score:.4f} confidence={decision.confidence:.4f} pass_gate={decision.pass_gate}"
        )

    print("\nCertification report:")
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))

    if args.strict and not report.meets_threshold:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
