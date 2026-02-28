from __future__ import annotations

from collections import Counter

from .memory_types import MemoryNode, Reminder, utc_now


class HabitEngine:
    def detect_habits(self, episodic_nodes: list[MemoryNode], min_repeats: int = 3) -> list[dict[str, str]]:
        phrases = [" ".join(node.text.lower().split()) for node in episodic_nodes if node.text.strip()]
        counts = Counter(phrases)
        habits: list[dict[str, str]] = []
        for phrase, count in counts.items():
            if count >= min_repeats:
                habits.append(
                    {
                        "habit_id": f"habit_{abs(hash(phrase)) % 10_000_000}",
                        "pattern": phrase,
                        "repeat_count": str(count),
                        "status": "proposed",
                    }
                )
        return habits

    def habit_to_reminder(self, *, user_id: str, agent_id: str, pattern: str, due_at=None) -> Reminder:
        return Reminder(
            user_id=user_id,
            agent_id=agent_id,
            title=f"Habit reminder: {pattern[:64]}",
            description="Auto-generated from repeated episodic memory pattern.",
            due_at=due_at or utc_now(),
            trigger_type="time",
            payload={"habit_pattern": pattern},
        )
