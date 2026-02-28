from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "agi1" / "supervisors" / "1000_agent_network.py"


spec = importlib.util.spec_from_file_location("supervisor_network", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TestSupervisorNetwork(unittest.TestCase):
    def test_swarm_simulation_assigns_leader(self) -> None:
        report = module.simulate_swarm(1000)
        self.assertEqual(report["total_supervisors"], 1000)
        self.assertTrue(report["leader"].startswith("sup_"))
        self.assertGreaterEqual(report["assigned_nodes"], 1)


if __name__ == "__main__":
    unittest.main()
