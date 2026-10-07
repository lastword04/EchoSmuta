import logging
import asyncio
from typing import Awaitable, Callable, Protocol
from pydantic import ValidationError
from shared.schemas.deal_events import DealEventSchema

from .subscriber import RedisSubscriberProtocol
from ..services.publisher import RedisPublisherProtocol
from ..services.messages import MessageServiceProtocol
from ..schemas import MessageRequestSchema
from ..enums import MessageType
from ....core.db import AsyncSession
from shared.services.templates import TextTemplateServiceProtocol

logger = logging.getLogger(__name__)


class DealEventHandlerProtocol(Protocol):
    async def handle_deal_event(self, event_data: dict) -> Awaitable[None]:
        ...

    async def start_listening(self) -> None:
        ...

    async def stop_listening(self) -> None:
        ...


class DealEventHandler(DealEventHandlerProtocol):
    def __init__(
        self,
        subscriber: RedisSubscriberProtocol,
        publisher: RedisPublisherProtocol,
        message_service_factory: Callable[[AsyncSession], MessageServiceProtocol],
        template_service: TextTemplateServiceProtocol,
    ):
        self.subscriber = subscriber
        self.publisher = publisher
        self.message_service_factory = message_service_factory
        self.template_service = template_service
        self._is_listening = False
        # Дедупликация по (deal_id, event_type) удалена: подписчик теперь единый
        # и последовательный (см. subscriber.py), дубликаты на этом уровне не
        # возникают. А повторные deal_confirmed/deal_accepted по той же сделке —
        # легитимные события (цикл "отмена → изменение → повторное подтверждение"),
        # которые раньше молча терялись в течение _dedup_ttl = 60 секунд —
        # именно из-за этого партнёр не видел статус "Партнёр подтвердил".

    async def handle_deal_event(self, event_data: dict) -> None:
        try:
            deal_event = DealEventSchema.model_validate(event_data["data"])

            # Шлём обоим участникам сделки
            for target_id in (str(deal_event.initiator_character_id), str(deal_event.partner_character_id)):
                message = {
                    "event_type": deal_event.event_type.value,
                    "data": {
                        "deal_id": str(deal_event.deal_id),
                        "initiator_character_id": str(deal_event.initiator_character_id) if deal_event.initiator_character_id else None,
                        "partner_character_id": str(deal_event.partner_character_id) if deal_event.partner_character_id else None,
                        "location_slug": deal_event.location_slug,
                        "details": deal_event.details,
                        "target_character_id": target_id,
                    }
                }
                await self.publisher.publish("chat_room_deals", message)

            # Системные сообщения — каждое только своему адресату
            if deal_event.details and deal_event.details.get("system_messages"):
                for sys_msg in deal_event.details["system_messages"]:
                    await self._create_system_message(sys_msg)

        except ValidationError as e:
            logger.error("Validation error for deal event: %s", e)
        except KeyError as e:
            logger.error("Missing key in deal event data: %s", e)
        except Exception as e:
            logger.error("Unexpected error handling deal event: %s", e)
            raise

    async def _create_system_message(self, sys_msg: dict) -> None:
        """Создаёт системное сообщение в чате."""
        from ....core.db import AsyncSessionFactory

        try:
            # Разбиваем ключ на части (trade_hall.deal.completed_money_ducats → ["trade_hall", "deal", "completed_money_ducats"])
            template_path = sys_msg["template_key"].split(".")

            # Рендерим шаблон
            content = self.template_service.get_template_by_path(
                template_path,
                **sys_msg["params"]
            )

            async with AsyncSessionFactory() as session:
                message_service = self.message_service_factory(session)
                message = MessageRequestSchema(
                    content=content,
                    target_user_ids=[sys_msg["character_id"]],
                    is_trade=False,
                    is_private=False,
                )

                await message_service.create_message_direct(
                    message_type=MessageType.SYSTEM_GLOBAL,
                    room="system",
                    message=message,
                    character_id=sys_msg["character_id"],
                )

            logger.debug("System message created for character %s: %s", sys_msg["character_id"], content)

        except Exception as e:
            logger.error("Failed to create system message: %s", e)

    async def start_listening(self) -> None:
        if self._is_listening:
            return
        await self.subscriber.subscribe("deals_events", self._route_event)
        self._is_listening = True
        logger.info("Started listening for deal events")

    async def stop_listening(self) -> None:
        if not self._is_listening:
            return
        if hasattr(self.subscriber, "stop"):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, "unsubscribe"):
            await self.subscriber.unsubscribe("deals_events")
        self._is_listening = False
        logger.info("Stopped listening for deal events")

    async def _route_event(self, event_data: dict) -> None:
        event_type = event_data.get("event_type")
        if not event_type:
            logger.warning("Deal event without event_type: %s", event_data)
            return
        await self.handle_deal_event(event_data)
