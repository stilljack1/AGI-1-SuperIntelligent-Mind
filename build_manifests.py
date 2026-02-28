#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
EXECUTIVE_MANIFESTS = [
    ROOT / "singularity_prime" / "governance" / "manifests" / "jack.json",
    ROOT / "singularity_prime" / "governance" / "manifests" / "julia.json",
    ROOT / "singularity_prime" / "governance" / "manifests" / "singularity.json",
    ROOT / "singularity_prime" / "governance" / "manifests" / "aegis.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = []
    for key in schema.get("required", []):
        if key not in payload:
            errors.append(f"missing:{key}")
    system_required = schema.get("properties", {}).get("system", {}).get("required", [])
    for key in system_required:
        if key not in payload.get("system", {}):
            errors.append(f"missing:system.{key}")
    if len(payload.get("executives", [])) < 4:
        errors.append("executives:minItems")
    return errors


def sign_manifest(payload: dict[str, Any], sign_key: str) -> dict[str, str]:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(sign_key.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return {"algorithm": "hmac-sha256", "value": signature}


def build(mode: str) -> dict[str, Any]:
    executives = [load_json(path) for path in EXECUTIVE_MANIFESTS]
    capability_evidence_path = ROOT / "agi1" / "runtime" / "capability_evidence.json"
    release_gates_path = ROOT / "agi1" / "runtime" / "release_gates_status.json"
    capability_evidence = load_json(capability_evidence_path) if capability_evidence_path.exists() else {}
    release_gates = load_json(release_gates_path) if release_gates_path.exists() else {}
    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "v1",
        "manifest_id": f"agi1-{mode}-{generated_at[:19].replace(':', '').replace('-', '')}",
        "mode": mode,
        "generated_at": generated_at,
        "system": {
            "name": "AGI-1",
            "version": "2026.02.28",
            "release_stage": "READY_FOR_VALIDATION" if mode == "staging" else "PRODUCTION_PREP",
        },
        "executives": [
            {
                "agent_id": item["agent_id"],
                "canonical_name": item["canonical_name"],
                "title": item["title"],
                "build_status": item["build_status"],
                "version": item["version"],
                "verified_capabilities": item.get("capabilities", {}).get("verified_capabilities", []),
            }
            for item in executives
        ],
        "capabilities": {
            "required": capability_evidence.get("required_capabilities", []),
            "evidence_overall": capability_evidence.get("overall", "UNKNOWN"),
            "release_gates_overall": release_gates.get("overall", "UNKNOWN"),
        },
        "versions": {
            "mobile": "0.1.0",
            "one_mind": "0.1.0",
            "agi_brain": "2026.02.24",
        },
        "evidence_paths": {
            "capability_evidence": str(capability_evidence_path),
            "release_gates": str(release_gates_path),
        },
    }
    sign_key = os.getenv("AGI1_MANIFEST_SIGN_KEY", "local-dev-manifest-sign-key")
    payload["signature"] = sign_manifest(payload, sign_key)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AGI-1 deployment manifests.")
    parser.add_argument("--mode", choices=["staging", "production"], default="production")
    parser.add_argument("--schema", default=str(ROOT / "manifest_schema.json"))
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    schema = load_json(Path(args.schema))
    payload = build(args.mode)
    errors = validate_manifest(payload, schema)
    if errors:
        raise SystemExit(f"Manifest validation failed: {errors}")

    output = Path(args.output) if args.output else ROOT / "runtime" / "generated_manifests" / f"{args.mode}_deployment_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "manifest_id": payload["manifest_id"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
