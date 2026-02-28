from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGI_CORE = ROOT / "agi-core"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(AGI_CORE) not in sys.path:
    sys.path.insert(0, str(AGI_CORE))

from runtime.cognitive_loop import AGI1CognitiveLoop  # noqa: E402


class TestAGICognitiveLoop(unittest.TestCase):
    def test_run_cycle_persists_dashboard_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            for name in [
                "runtime",
                "perception",
                "memory",
                "world_model",
                "reasoning",
                "planning",
                "learning",
                "feedback",
                "self_model",
                "consciousness",
                "safety",
                "interfaces",
                "architecture",
            ]:
                (root / name).mkdir(parents=True, exist_ok=True)
            loop = AGI1CognitiveLoop(root=root)
            payload = loop.run_cycle(raw_input="Build AGI-1 planning memory and verify the result.")
            self.assertEqual(payload["cycle_id"], 1)
            self.assertTrue(payload["execution"]["success"])
            self.assertIn("strategic", payload)
            self.assertIn("belief_update", payload)
            self.assertIn("alignment", payload)
            self.assertIn("research", payload)
            dashboard = json.loads((root / "runtime" / "state" / "dashboard_state.json").read_text(encoding="utf-8"))
            self.assertEqual(dashboard["cycle_id"], 1)
            self.assertGreaterEqual(dashboard["memory_summary"]["goals"], 1)


if __name__ == "__main__":
    unittest.main()
