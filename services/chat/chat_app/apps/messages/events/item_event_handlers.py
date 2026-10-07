import logging
from typing import Awaitable, Callable, Protocol

from pydantic import ValidationError
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from .subscriber import RedisSubscriberProtocol
from ..enums import MessageType
from ..schemas import MessageRequestSchema
from ..services.messages import MessageServiceProtocol
from ....core.db import AsyncSession, AsyncSessionFactory
from ..adapter.characters import CharacterServiceClientProtocol

logger = logging.getLogger(__name__)


class ItemEventHandlerProtocol(Protocol):
    async def handle_item_event(self, event_data: dict) -> Awaitable[None]:
        ...

    async def start_listening(self) -> None:
        ...

    async def stop_listening(self) -> None:
        ...


class ItemEventHandler(ItemEventHandlerProtocol):
    def __init__(
        self,
        subscriber: RedisSubscriberProtocol,
        message_service_factory: Callable[[AsyncSession], MessageServiceProtocol],
        character_service: CharacterServiceClientProtocol,
    ):
        self.subscriber = subscriber
        self.message_service_factory = message_service_factory
        self.character_service = character_service
        self._is_listening = False

    async def handle_item_event(self, event_data: dict) -> None:
        async with AsyncSessionFactory() as session:
            try:
                message_service = self.message_service_factory(session)
                item_event = ItemMessageEventSchema.model_validate(event_data["data"])

                target_user_ids = await self._resolve_target_user_ids(item_event)
                message_type = self._get_message_type(item_event.scope)

                message = MessageRequestSchema(
                    content=item_event.content,
                    target_user_ids=target_user_ids,
                    is_trade=item_event.is_trade,
                    is_private=False,
                )

                await message_service.create_message_direct(
                    message_type=message_type,
                    room="system",
                    message=message,
                    character_id=item_event.character_id,
                )

            except ValidationError as e:
                logger.error("Validation error for items event: %s", e)
            except KeyError as e:
                logger.error("Missing key in items event data: %s", e)
            except Exception as e:
                logger.error("Unexpected error handling items event: %s", e)
                raise

    async def start_listening(self) -> None:
        if self._is_listening:
            return

        await self.subscriber.subscribe("items_events", self._route_event)
        self._is_listening = True
        logger.info("Started listening for items events")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return

        if hasattr(self.subscriber, "stop"):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, "unsubscribe"):
            await self.subscriber.unsubscribe("items_events")

        self._is_listening = False
        logger.info("Stopped listening for items events")

    async def _route_event(self, event_data: dict) -> None:
        event_type = event_data.get("event_type")
        if not event_type:
            logger.warning("Items event without event_type: %s", event_data)
            return

        await self.handle_item_event(event_data)

    async def _resolve_target_user_ids(self, item_event: ItemMessageEventSchema) -> list | None:
        # Для PRIVATE — используем уже заданный список
        if item_event.scope == ItemMessageScope.PRIVATE:
            return item_event.target_user_ids

        # Для CITY — получаем всех жителей города, кроме автора
        if item_event.scope == ItemMessageScope.CITY:
            try:
                all_ids = await self.character_service.get_character_ids_by_location(
                    item_event.location_slug
                )
            except Exception as e:
                # Ошибку логируем (сработает только при поломке) и не шлём никому
                logger.error("CITY: ошибка запроса by-location для %s: %s", item_event.location_slug, e)
                return []

            return [uid for uid in all_ids if uid != item_event.character_id]

        return item_event.target_user_ids

    def _get_message_type(self, scope: ItemMessageScope) -> MessageType:
        if scope == ItemMessageScope.PRIVATE:
            return MessageType.SYSTEM_PRIVATE

        return MessageType.SYSTEM_GLOBAL
