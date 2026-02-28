from __future__ import annotations

import unittest

from scripts.autonomous_orchestration import orchestrate


class TestAutonomousOrchestration(unittest.TestCase):
    def test_orchestration_report_shape(self) -> None:
        payload = orchestrate(
            supervisors=25,
            duration=10,
            bridge_host="127.0.0.1",
            status_port=6553,
            stream_port=6554,
            job="process platform logic",
        )
        self.assertIn("supervisors", payload)
        self.assertIn("research_lab", payload)
        self.assertIn("render_railway_bus", payload)
        self.assertIn("bridge", payload)


if __name__ == "__main__":
    unittest.main()
