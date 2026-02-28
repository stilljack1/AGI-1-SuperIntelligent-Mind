from __future__ import annotations

from typing import Any


class PatternSynthesizer:
    def synthesize(self, *, abstraction: dict[str, Any], analogy: dict[str, Any]) -> dict[str, Any]:
        return {
            "synthesis": f"{abstraction['pattern']} interpreted through {analogy['analogy']}",
            "transferable_rule": "prefer reversible actions before irreversible commitments",
        }
