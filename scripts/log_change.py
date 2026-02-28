#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from agi1_core.changelog_logger import ChangelogLogger


def default_changed_files() -> list[str]:
    try:
        output = subprocess.check_output(["git", "status", "--short"], text=True)
        files = []
        for line in output.splitlines():
            if not line.strip():
                continue
            files.append(line[3:].strip())
        return files
    except Exception:  # noqa: BLE001
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Append structured entry to ~/agi-factory/CHANGELOG.md")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--tests", nargs="*", default=[])
    args = parser.parse_args()

    files = args.files or default_changed_files()
    tests = args.tests

    logger = ChangelogLogger()
    path = logger.append_simple(summary=args.summary, files_changed=files, tests_run=tests)
    print(str(Path(path).expanduser()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
