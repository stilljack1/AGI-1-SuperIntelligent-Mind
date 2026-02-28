from __future__ import annotations

from datetime import datetime
from typing import Any

from .memory_types import Reminder, utc_now
from .stores.interfaces import ReminderStore


class ReminderService:
    def __init__(self, store: ReminderStore) -> None:
        self.store = store

    def create_reminder(self, reminder: Reminder) -> Reminder:
        if reminder.due_at is None and not reminder.cron and not reminder.condition:
            raise ValueError("reminder_requires_due_at_or_condition")
        return self.store.create_reminder(reminder)

    def get_due_reminders(self, *, user_id: str, now: datetime | None = None, limit: int = 50) -> list[Reminder]:
        now = now or utc_now()
        due = self.store.due_reminders(now=now, user_id=user_id, limit=limit)
        fired: list[Reminder] = []
        for item in due:
            updated = self.store.ack_reminder(item.reminder_id, status="fired")
            fired.append(updated or item)
        return fired

    def ack_reminder(self, reminder_id: str) -> Reminder | None:
        return self.store.ack_reminder(reminder_id, status="acked")

    @staticmethod
    def evaluate_conditions(event: dict[str, Any], condition: str | None) -> bool:
        if not condition:
            return False
        text = condition.strip()
        if not text:
            return False
        if "==" in text:
            key, expected = [part.strip() for part in text.split("==", 1)]
            return str(event.get(key, "")).strip() == expected
        if ":" in text:
            key, expected = [part.strip() for part in text.split(":", 1)]
            return expected.lower() in str(event.get(key, "")).lower()
        return text.lower() in str(event).lower()
