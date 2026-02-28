from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.models import AGIMessage


@dataclass
class MessageBus:
    queue: list[AGIMessage] = field(default_factory=list)

    def publish(
        self,
        *,
        sender: str,
        receiver: str,
        intent: str,
        data: dict[str, Any],
        confidence: float,
        priority: float,
    ) -> AGIMessage:
        message = AGIMessage(
            sender=sender,
            receiver=receiver,
            intent=intent,
            data=data,
            confidence=confidence,
            priority=priority,
        )
        self.queue.append(message)
        self.queue.sort(key=lambda item: (item.priority, item.confidence), reverse=True)
        return message

    def dispatch(self, *, receiver: str, limit: int = 10) -> list[dict[str, Any]]:
        delivered = [message for message in self.queue if message.receiver == receiver][:limit]
        delivered_ids = {id(message) for message in delivered}
        self.queue = [message for message in self.queue if id(message) not in delivered_ids]
        return [message.to_dict() for message in delivered]
