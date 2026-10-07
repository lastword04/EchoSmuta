import uuid
import logging
from typing import Protocol, Callable
from ....core.db import AsyncSession, AsyncSessionFactory
from .subscriber import RedisSubscriberProtocol
from ..services.tokens import TokenServiceProtocol

logger = logging.getLogger(__name__)


class AuthCharacterEventHandlerProtocol(Protocol):
    async def handle_character_banned(self, event_data: dict) -> None: ...
    async def handle_character_unbanned(self, event_data: dict) -> None: ...
    async def start_listening(self) -> None: ...
    async def stop_listening(self) -> None: ...


class AuthCharacterEventHandler(AuthCharacterEventHandlerProtocol):
    def __init__(
        self,
        subscriber: RedisSubscriberProtocol,
        token_service_factory: Callable[[AsyncSession], TokenServiceProtocol],
    ):
        self.subscriber = subscriber
        self.token_service_factory = token_service_factory
        self._is_listening = False

    async def handle_character_banned(self, event_data: dict) -> None:
        """Бан персонажа: инвалидируем все его refresh tokens"""
        try:
            character_id = uuid.UUID(event_data["data"]["character_id"])
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid character_banned event data: {e}")
            return

        try:
            async with AsyncSessionFactory() as session:
                token_service = self.token_service_factory(session)
                await token_service.delete_all_by_character_id(character_id)
            logger.info(f"Invalidated all refresh tokens for banned character {character_id}")
        except Exception as e:
            logger.error(f"Error invalidating tokens for character {character_id}: {e}")

    async def handle_character_unbanned(self, event_data: dict) -> None:
        """Разбан: токены не восстанавливаем — пользователь логинится заново"""
        try:
            character_id = uuid.UUID(event_data["data"]["character_id"])
            logger.info(f"Character {character_id} unbanned. User must login again.")
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid character_unbanned event data: {e}")

    async def start_listening(self) -> None:
        if self._is_listening:
            return
        await self.subscriber.subscribe("character_events", self._route_event)
        self._is_listening = True
        logger.info("Started listening for character events")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return
        if hasattr(self.subscriber, 'stop'):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, 'unsubscribe'):
            await self.subscriber.unsubscribe("character_events")
        self._is_listening = False
        logger.info("Stopped listening for character events")

    async def _route_event(self, event_data: dict) -> None:
        event_type = event_data.get("event_type")
        handlers = {
            "character_banned": self.handle_character_banned,
            "character_unbanned": self.handle_character_unbanned,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)