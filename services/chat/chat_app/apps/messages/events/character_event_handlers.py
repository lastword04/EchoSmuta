import logging
import uuid
from typing import Protocol, Awaitable, Callable
from pydantic import ValidationError
from shared.schemas.characters import CharacterReadSchema
from shared.services.templates import TextTemplateServiceProtocol
from .subscriber import RedisSubscriberProtocol
from ..services.publisher import RedisPublisherProtocol
from ..services.messages import MessageServiceProtocol
from ..schemas import MessageRequestSchema
from ..enums import MessageType
from ...categories.services.visibility_notifications import CheckVisibilityNotificationsServiceProtocol
from ....core.db import AsyncSession, AsyncSessionFactory

logger = logging.getLogger(__name__)


class CharacterEventHandlerProtocol(Protocol):
    async def handle_character_played(self, event_data: dict) -> Awaitable[None]: ...
    async def handle_character_banned(self, event_data: dict) -> Awaitable[None]: ...
    async def handle_character_unbanned(self, event_data: dict) -> Awaitable[None]: ...
    async def start_listening(self) -> None: ...
    async def stop_listening(self) -> None: ...


class CharacterEventHandler(CharacterEventHandlerProtocol):
    def __init__(
        self,
        subscriber: RedisSubscriberProtocol,
        publisher: RedisPublisherProtocol,
        template_service: TextTemplateServiceProtocol,
        message_service_factory: Callable[[AsyncSession], MessageServiceProtocol],
        visibility_service_factory: Callable[[AsyncSession], CheckVisibilityNotificationsServiceProtocol]
    ):
        self.subscriber = subscriber
        self.publisher = publisher
        self.template_service = template_service
        self.message_service_factory = message_service_factory
        self.visibility_service_factory = visibility_service_factory
        self._is_listening = False

    async def handle_character_played(self, event_data: dict) -> None:
        """Обработка события захода персонажа в игру"""
        async with AsyncSessionFactory() as session:
            try:
                message_service = self.message_service_factory(session)
                visibility_service = self.visibility_service_factory(session)
                character_data = event_data["data"]

                character = CharacterReadSchema.model_validate(character_data)

                gender_str = "male" if character.is_male else "female"
                template_key = f"character_play_friends_{gender_str}"
                content_message = self.template_service.get_template(template_key)
                target_user_ids = await visibility_service.get_notification_receivers_for_target(character.id)
                message = MessageRequestSchema(
                    content=content_message,
                    target_user_ids=target_user_ids,
                    is_trade=False,
                    is_private=False
                )
                await message_service.create_message_direct(
                    message_type=MessageType.SYSTEM_PLAY_CHARACTER,
                    room="system",
                    message=message,
                    character_id=character.id
                )

            except ValidationError as e:
                logger.error(f"Validation error for character data: {e}")
            except KeyError as e:
                logger.error(f"Missing key in event data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error handling character_played: {e}")
                raise

    async def handle_character_banned(self, event_data: dict) -> None:
        """Бан: отправляем force_disconnect в персональный Redis канал"""
        try:
            character_id = uuid.UUID(event_data["data"]["character_id"])
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid character_banned event data: {e}")
            return

        try:
            await self.publisher.publish(
                f"force_disconnect_{character_id}",
                {
                    "event_type": "force_disconnect",
                    "reason": "Вы забанены администратором"
                }
            )
            logger.info(f"Sent force_disconnect for banned character {character_id}")
        except Exception as e:
            logger.error(f"Error publishing force_disconnect for {character_id}: {e}")

    async def handle_character_unbanned(self, event_data: dict) -> None:
        """Разбан: просто логируем (токены уже инвалидированы auth'ом)"""
        try:
            character_id = uuid.UUID(event_data["data"]["character_id"])
            logger.info(f"Character {character_id} unbanned (no action needed in chat)")
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
            "character_played": self.handle_character_played,
            "character_banned": self.handle_character_banned,
            "character_unbanned": self.handle_character_unbanned,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.debug(f"Unknown event type: {event_type}")