import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Protocol

from pydantic import ValidationError

from shared.schemas.characters import CharacterChangeLocationEvent

from .....core.db import AsyncSession, AsyncSessionFactory
from ...services.crafting.items_creating_actions import (
    CancelItemsCreatingProcessServiceProtocol,
)
from .subscriber import RedisSubscriberProtocol

logger = logging.getLogger(__name__)

# Локации воркшопов: если персонаж УШЁЛ из одной из них — отменяем крафт
WORKSHOP_LOCATION_SLUGS = {
    "1.35.laboratory",
    "1.36.kitchen",
    "1.37.carpentry-workshop",
    "1.38.hunter-workshop",
    "1.39.incubator",
    "1.13.forge",
    "1.16.jewelers",
}


class CraftingEventHandlerProtocol(Protocol):
    async def handle_character_quit(self, event_data: dict) -> Awaitable[None]: ...
    async def handle_character_change_location(self, event_data: dict) -> Awaitable[None]: ...
    async def start_listening(self) -> None: ...
    async def stop_listening(self) -> None: ...


class CraftingEventHandler(CraftingEventHandlerProtocol):
    def __init__(
        self,
        subscriber: RedisSubscriberProtocol,
        crafting_service_factory: Callable[[AsyncSession], CancelItemsCreatingProcessServiceProtocol],
    ):
        self.subscriber = subscriber
        self.crafting_service_factory = crafting_service_factory
        self._is_listening = False

    async def handle_character_quit(self, event_data: dict) -> Awaitable[None]:
        """Выход персонажа из игры — отменяем активный крафт"""
        async with AsyncSessionFactory() as session:
            try:
                crafting_service = self.crafting_service_factory(session)
                character_id = uuid.UUID(event_data["data"])
                await crafting_service.cancel_creating(character_id)
                logger.info("Crafting cancelled for character %s (quit)", character_id)
            except KeyError as e:
                logger.error(f"Missing key in quit event data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error handling quit for crafting: {e}")

    async def handle_character_change_location(self, event_data: dict) -> Awaitable[None]:
        """Смена локации: если персонаж ушёл из воркшопа — отменяем крафт"""
        async with AsyncSessionFactory() as session:
            try:
                location = CharacterChangeLocationEvent.model_validate(event_data["data"])
                old_slug = getattr(location.old_location, "slug", None)
                new_slug = getattr(location.new_location, "slug", None)

                if old_slug in WORKSHOP_LOCATION_SLUGS and new_slug not in WORKSHOP_LOCATION_SLUGS:
                    crafting_service = self.crafting_service_factory(session)
                    await crafting_service.cancel_creating(location.character_id)
                    logger.info(
                        "Crafting cancelled for character %s (left workshop %s -> %s)",
                        location.character_id, old_slug, new_slug,
                    )
            except ValidationError as e:
                logger.error(f"Validation error for change_location (crafting): {e}")
            except KeyError as e:
                logger.error(f"Missing key in change_location event data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error handling change_location for crafting: {e}")

    async def start_listening(self) -> None:
        if self._is_listening:
            return
        await self.subscriber.subscribe("change_location", self._route_event)
        self._is_listening = True
        logger.info("Started listening for crafting events")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return
        if hasattr(self.subscriber, "stop"):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, "unsubscribe"):
            await self.subscriber.unsubscribe("change_location")
        self._is_listening = False
        logger.info("Stopped listening for crafting events")

    async def _route_event(self, event_data: dict) -> None:
        event_type = event_data.get("event_type")
        handlers = {
            "quit": self.handle_character_quit,
            "change_location": self.handle_character_change_location,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.warning(f"Unknown event type for crafting handler: {event_type}")