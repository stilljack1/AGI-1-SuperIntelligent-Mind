from __future__ import annotations

import argparse
import json
from pathlib import Path

from .memory_os import MemoryOS


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MemoryOS background pruning.")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    memory = MemoryOS.from_env(db_path=args.db_path)
    report = memory.run_tiering(user_id=args.user_id)
    output = Path(args.output) if args.output else Path(args.db_path).with_name("memory_pruner_report.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
