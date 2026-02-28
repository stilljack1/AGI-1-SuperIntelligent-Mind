from __future__ import annotations

import unittest
from pathlib import Path

from agi1_autonomous_os.lab.run import run_lab


class TestLabRunCLI(unittest.TestCase):
    def test_lab_run_returns_35_results(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = root / "agi1_autonomous_os" / "lab" / "manifest_35_agents.json"
        payload = run_lab(manifest_path=manifest, job="summarize alignment gaps")
        self.assertEqual(payload["agent_count"], 35)
        self.assertEqual(len(payload["results"]), 35)


if __name__ == "__main__":
    unittest.main()
