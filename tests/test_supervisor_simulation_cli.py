from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agi1.supervisors.simulate import run_simulation


class TestSupervisorSimulationCLI(unittest.TestCase):
    def test_simulation_emits_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = run_simulation(total=25, duration=10)
            self.assertEqual(payload["supervisors"], 25)
            self.assertIn("consensus_success_pct", payload)
            output = Path(tmp_dir) / "report.json"
            output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
