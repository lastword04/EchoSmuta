import logging
from typing import Protocol, Awaitable, Callable
from pydantic import ValidationError
from shared.schemas.mining import MonsterAttackEventSchema
from .subscriber import RedisSubscriberProtocol
from ..services.messages import MessageServiceProtocol
from shared.services.templates import TextTemplateServiceProtocol
from ..schemas import MessageRequestSchema
from ..enums import MessageType
from ....core.db import AsyncSession, AsyncSessionFactory

logger = logging.getLogger(__name__)

class MonsterEventHandlerProtocol(Protocol):
    async def handle_monster_attack(self, event_data: dict) -> Awaitable[None]: 
        ...

    async def handle_monster_attack_win(self, event_data: dict) -> Awaitable[None]: 
        ...

    async def start_listening(self) -> None:
        ...

    async def stop_listening(self) -> None:
        ...

class MonsterEventHandler(MonsterEventHandlerProtocol):
    def __init__(self, subscriber: RedisSubscriberProtocol, 
                 message_service_factory: Callable[[AsyncSession], MessageServiceProtocol], 
                 template_service: TextTemplateServiceProtocol):
        self.subscriber = subscriber
        self.message_service_factory = message_service_factory
        self.template_service = template_service
        self._is_listening = False
    
    async def handle_monster_attack(self, event_data: dict) -> None:
        """Обработка события с валидацией и обработкой ошибок"""
        async with AsyncSessionFactory() as session:

            try:
                message_service = self.message_service_factory(session)
                monster_data = event_data["data"]
                
                # Валидация данных
                monster = MonsterAttackEventSchema.model_validate(monster_data)
                location = monster.location_slug.split('.')[-1]
                template_key = f"mining_locations_{location}_monsters_attack"

                content_message = self.template_service.get_template(template_key)
                target_user_ids=[monster.character_id]
                message = MessageRequestSchema(
                    content=content_message,
                    target_user_ids=target_user_ids,
                    is_trade=False,
                    is_private=False
                )
                await message_service.create_message_direct(
                    message_type=MessageType.SYSTEM_PRIVATE,
                    room="system",
                    message=message,
                    character_id=monster.character_id
                )
                
            except ValidationError as e:
                logger.error(f"Validation error for monster data: {e}")
                logger.debug(f"Invalid data: {monster_data}")
                # Можно отправить событие об ошибке или обработать иначе
                
            except KeyError as e:
                logger.error(f"Missing key in event data: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error handling monster_attack: {e}")
                raise

    async def handle_monster_attack_win(self, event_data: dict) -> None:
        """Обработка события с валидацией и обработкой ошибок"""
        async with AsyncSessionFactory() as session:

            try:
                message_service = self.message_service_factory(session)

                monster_data = event_data["data"]
                
                # Валидация данных
                monster = MonsterAttackEventSchema.model_validate(monster_data)
                location = monster.location_slug.split('.')[-1]
                status_monster = "standard" if monster.is_standart_monster else "improved"
                template_key = f"mining_locations_{location}_monsters_loot_{status_monster}"

                content_message = self.template_service.get_template(template_key)
                target_user_ids=[monster.character_id]
                message = MessageRequestSchema(
                    content=content_message,
                    target_user_ids=target_user_ids,
                    is_trade=False,
                    is_private=False
                )
                await message_service.create_message_direct(
                    message_type=MessageType.SYSTEM_PRIVATE,
                    room="system",
                    message=message,
                    character_id=monster.character_id
                )
                
            except ValidationError as e:
                logger.error(f"Validation error for monster data: {e}")
                logger.debug(f"Invalid data: {monster_data}")
                # Можно отправить событие об ошибке или обработать иначе
                
            except KeyError as e:
                logger.error(f"Missing key in event data: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error handling monster_attack_win: {e}")
                raise
    
    async def start_listening(self) -> None:
        """Запуск прослушивания событий"""
        if self._is_listening:
            return
            
        await self.subscriber.subscribe("monster_attack", self._route_event)
        self._is_listening = True
        logger.info("Started listening for monster attack events")
    
    async def stop_listening(self) -> None:
        """Остановка прослушивания событий"""
        if not self._is_listening:
            return
            
        if hasattr(self.subscriber, 'stop'):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, 'unsubscribe'):
            await self.subscriber.unsubscribe("monster_attack")
            
        self._is_listening = False
        logger.info("Stopped listening for monster attack events")
    
    async def _route_event(self, event_data: dict) -> None:
        """Маршрутизация событий на соответствующие обработчики"""
        event_type = event_data.get("event_type")
        
        handlers = {
            "monster_attack_process": self.handle_monster_attack,
            "monster_attack_success": self.handle_monster_attack_win,

        }
        
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")