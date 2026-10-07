import logging
from typing import Awaitable, Protocol
from .subscriber import RedisSubscriberProtocol
from ..services.publisher import RedisPublisherProtocol

logger = logging.getLogger(__name__)


class CharacterPresenceHandlerProtocol(Protocol):
    async def start_listening(self) -> None: ...
    async def stop_listening(self) -> None: ...


class CharacterPresenceHandler(CharacterPresenceHandlerProtocol):
    def __init__(
        self,
        subscriber_online: RedisSubscriberProtocol,
        subscriber_location: RedisSubscriberProtocol,
        publisher: RedisPublisherProtocol,
    ):
        self.subscriber_online = subscriber_online
        self.subscriber_location = subscriber_location
        self.publisher = publisher
        self._is_listening = False

    async def start_listening(self) -> None:
        if self._is_listening:
            return

        await self.subscriber_online.subscribe("online_status_changed", self._handle_online_status)
        await self.subscriber_location.subscribe("change_location", self._handle_change_location)
        self._is_listening = True
        logger.info("Character presence handler started listening")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return

        if hasattr(self.subscriber_online, "stop"):
            await self.subscriber_online.stop()
        if hasattr(self.subscriber_location, "stop"):
            await self.subscriber_location.stop()
        if hasattr(self.subscriber_online, "unsubscribe"):
            await self.subscriber_online.unsubscribe("online_status_changed")
        if hasattr(self.subscriber_location, "unsubscribe"):
            await self.subscriber_location.unsubscribe("change_location")

        self._is_listening = False

    async def _handle_online_status(self, event_data: dict) -> None:
        """Обработка события входа/выхода из игры"""
        try:
            if not isinstance(event_data, dict):
                logger.warning("online_status_changed: event_data is not a dict: %r", event_data)
                return
            data = event_data.get("data", {})
            if not isinstance(data, dict) or not data:
                return

            character_id = data.get("character_id")
            is_online = data.get("is_online")
            location_slug = data.get("location_slug")

            if not character_id:
                return

            current_room_id = data.get("current_room_id")

            message = {
                "event_type": "character_online",
                "character_id": character_id,
                "is_online": is_online,
                "location_slug": location_slug,
                "current_room_id": current_room_id,
                "name": data.get("name"),
                "level": data.get("level"),
                "race": data.get("race"),
                "user_data": {
                    "id": character_id,
                    "name": data.get("name"),
                    "level": data.get("level"),
                    "race": data.get("race"),
                    "location_slug": location_slug,
                    "current_room_id": current_room_id,
                    "is_online": is_online,
                    "is_ignored": data.get("is_ignored", False),
                }
            }

            await self.publisher.publish("chat_room_presence", message)
            logger.debug("Presence event published: character %s is_online=%s", character_id, is_online)

        except Exception as e:
            logger.error("Error handling online_status_changed: %s", e)

    async def _handle_change_location(self, event_data: dict) -> None:
        try:
            if not isinstance(event_data, dict):
                logger.warning("change_location: event_data is not a dict: %r", event_data)
                return
            data = event_data.get("data", {})
            if not isinstance(data, dict) or not data:
                return
            character_id = data.get("character_id")
            if not character_id:
                return

            old_location = data.get("old_location") or {}
            new_location = data.get("new_location") or {}
            if not isinstance(old_location, dict):
                old_location = {}
            if not isinstance(new_location, dict):
                new_location = {}

            message = {
                "event_type": "character_location",
                "character_id": character_id,
                "old_location_slug": old_location.get("slug"),
                "new_location_slug": new_location.get("slug"),
                "old_real_location_slug": data.get("old_real_location_slug"),
                "new_real_location_slug": data.get("new_real_location_slug"),
                "name": data.get("name"),
                "level": data.get("level"),
                "race": data.get("race"),
                "user_data": {
                    "id": character_id,
                    "name": data.get("name"),
                    "level": data.get("level"),
                    "race": data.get("race"),
                    "location_slug": new_location.get("slug"),
                    "is_online": True,
                    "is_ignored": data.get("is_ignored", False),
                }
            }
            await self.publisher.publish("chat_room_presence", message)
            logger.debug("Location change event published: character %s", character_id)
        except Exception as e:
            logger.error("Error handling change_location: %s", e)