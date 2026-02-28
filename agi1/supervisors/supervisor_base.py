from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupervisorBase:
    supervisor_id: str
    tier: str
    assigned_tasks: list[str] = field(default_factory=list)

    def assign(self, task_id: str) -> None:
        self.assigned_tasks.append(task_id)

    def status(self) -> dict[str, Any]:
        return {
            "supervisor_id": self.supervisor_id,
            "tier": self.tier,
            "assigned_count": len(self.assigned_tasks),
        }

