import logging
import uuid
from typing import Protocol
from datetime import datetime, timezone
from .publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)

class MailNotificationEventsProtocol(Protocol):
    async def publish_mail_created(self, recipient_id: uuid.UUID, sender_name: str, message_preview: str) -> None:
        ...

class MailNotificationEvents(MailNotificationEventsProtocol):
    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish_mail_created(self, recipient_id: uuid.UUID, sender_name: str, message_preview: str) -> None:
        """Публикация события создания нового письма"""
        event_data = {
            "event_type": "new_mail",
            "data": {
                "recipient_id": str(recipient_id),
                "sender_name": sender_name,
                "message_preview": message_preview[:100] if message_preview else ""
            },
            "timestamp": self._get_timestamp()
        }
        channel = f"mail_notifications_{recipient_id}"
        await self.publisher.publish(channel, event_data)
        logger.info(f"Published new_mail event for recipient {recipient_id}")

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()