from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class RoutedAssignment:
    task_id: str
    supervisor_id: str


class SupervisorRouter:
    def __init__(self, total_supervisors: int = 1000) -> None:
        self.total_supervisors = total_supervisors

    def route(self, task_id: str) -> RoutedAssignment:
        digest = sha256(task_id.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % self.total_supervisors
        supervisor_id = f"sup_{index:04d}"
        return RoutedAssignment(task_id=task_id, supervisor_id=supervisor_id)

