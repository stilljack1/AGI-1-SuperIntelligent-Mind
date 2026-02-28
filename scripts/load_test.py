from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class LoadResult:
    latency_ms: float
    ok: bool
    status_code: int
    error: str = ""


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1, int(round((percentile / 100.0) * (len(sorted_values) - 1)))))
    return sorted_values[idx]


async def _worker(
    *,
    worker_id: int,
    iterations: int,
    inject_failure_rate: float,
    client: httpx.AsyncClient,
) -> list[LoadResult]:
    results: list[LoadResult] = []
    for iteration in range(iterations):
        started = time.perf_counter()
        try:
            session_resp = await client.post(
                "/v1/sessions",
                json={
                    "user_id": f"load-user-{worker_id}",
                    "input_lang": "en",
                    "output_lang": "en",
                    "auto_detect": False,
                },
            )
            if session_resp.status_code != 200:
                elapsed = (time.perf_counter() - started) * 1000.0
                results.append(
                    LoadResult(
                        latency_ms=elapsed,
                        ok=False,
                        status_code=session_resp.status_code,
                        error=f"session_create_failed:{session_resp.text[:200]}",
                    )
                )
                continue

            session_payload = session_resp.json()
            token = session_payload["token"]
            if random.random() < inject_failure_rate:
                token = "invalid-token"

            run_resp = await client.post(
                "/v1/task/execute",
                json={
                    "session_id": session_payload["session_id"],
                    "token": token,
                    "task": f"load-test task {worker_id}-{iteration}",
                    "agent_id": "singularity",
                    "agent_name": "Singularity",
                    "current_task": "load_probe",
                    "logs": [],
                    "selected_industry": "technology",
                    "input_lang": "en",
                    "output_lang": "en",
                    "style_preset": "trust",
                    "whisper_mode": False,
                },
            )
            elapsed = (time.perf_counter() - started) * 1000.0
            results.append(
                LoadResult(
                    latency_ms=elapsed,
                    ok=run_resp.status_code == 200,
                    status_code=run_resp.status_code,
                    error="" if run_resp.status_code == 200 else run_resp.text[:200],
                )
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = (time.perf_counter() - started) * 1000.0
            results.append(LoadResult(latency_ms=elapsed, ok=False, status_code=0, error=str(exc)))
    return results


async def run_load_test(
    *,
    base_url: str,
    concurrency: int,
    iterations_per_worker: int,
    inject_failure_rate: float,
    inprocess: bool,
) -> dict[str, Any]:
    transport: Optional[httpx.AsyncBaseTransport] = None
    if inprocess:
        sys.path.insert(0, str(ROOT / "apps" / "api"))
        sys.path.insert(0, str(ROOT / "packages" / "core" / "src"))
        sys.path.insert(0, str(ROOT / "packages" / "memory" / "voice_profiles" / "src"))
        sys.path.insert(0, str(ROOT / "packages"))
        from app.main import create_app  # noqa: WPS433

        transport = httpx.ASGITransport(app=create_app())
        base_url = "http://testserver"

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0, transport=transport) as client:
        tasks = [
            _worker(
                worker_id=idx,
                iterations=iterations_per_worker,
                inject_failure_rate=inject_failure_rate,
                client=client,
            )
            for idx in range(concurrency)
        ]
        matrix = await asyncio.gather(*tasks)

    rows = [item for worker_results in matrix for item in worker_results]
    latencies = sorted([row.latency_ms for row in rows])
    ok_count = sum(1 for row in rows if row.ok)
    total = len(rows)
    error_count = total - ok_count

    return {
        "pm": "OpenClaw",
        "exec": "Agent 1 Jack | Agent 2 Julia | Agent 3 Singularity | Agent 4 Aegis",
        "total_requests": total,
        "success_count": ok_count,
        "error_count": error_count,
        "success_rate": round(ok_count / total, 6) if total else 0.0,
        "latency_ms": {
            "min": round(min(latencies), 3) if latencies else 0.0,
            "p50": round(_percentile(latencies, 50), 3),
            "p95": round(_percentile(latencies, 95), 3),
            "p99": round(_percentile(latencies, 99), 3),
            "max": round(max(latencies), 3) if latencies else 0.0,
            "mean": round(statistics.mean(latencies), 3) if latencies else 0.0,
        },
        "errors": [row.error for row in rows if row.error][:20],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw API load and resilience test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--inject-failure-rate", type=float, default=0.05)
    parser.add_argument("--inprocess", action="store_true", help="Run against in-process FastAPI app")
    parser.add_argument("--target-p95-ms", type=float, default=2000.0)
    parser.add_argument("--target-success-rate", type=float, default=0.95)
    parser.add_argument("--enforce-slo", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = asyncio.run(
        run_load_test(
            base_url=args.base_url,
            concurrency=max(1, args.concurrency),
            iterations_per_worker=max(1, args.iterations),
            inject_failure_rate=max(0.0, min(1.0, args.inject_failure_rate)),
            inprocess=args.inprocess,
        )
    )
    print(json.dumps(report, indent=2))

    if args.enforce_slo:
        p95 = float(report["latency_ms"]["p95"])
        success_rate = float(report["success_rate"])
        if p95 > args.target_p95_ms or success_rate < args.target_success_rate:
            raise SystemExit(
                f"SLO breach: p95={p95:.2f}ms target={args.target_p95_ms:.2f}ms "
                f"success={success_rate:.3f} target={args.target_success_rate:.3f}"
            )


if __name__ == "__main__":
    main()
