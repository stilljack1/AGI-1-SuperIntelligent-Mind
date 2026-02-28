from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGI_CORE = ROOT / "agi-core"
if str(AGI_CORE) not in sys.path:
    sys.path.insert(0, str(AGI_CORE))

from runtime.message_protocol import MessageBus  # noqa: E402


class TestMessageProtocol(unittest.TestCase):
    def test_priority_dispatch(self) -> None:
        bus = MessageBus()
        bus.publish(
            sender="reasoning",
            receiver="planning",
            intent="candidate_a",
            data={"name": "a"},
            confidence=0.7,
            priority=0.4,
        )
        bus.publish(
            sender="safety",
            receiver="planning",
            intent="candidate_b",
            data={"name": "b"},
            confidence=0.8,
            priority=0.9,
        )
        delivered = bus.dispatch(receiver="planning")
        self.assertEqual(delivered[0]["intent"], "candidate_b")


if __name__ == "__main__":
    unittest.main()
