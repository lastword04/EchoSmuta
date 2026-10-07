import logging
import uuid
from typing import Protocol, Awaitable, Callable
from pydantic import ValidationError
from shared.schemas.mining import MiningActionEventSchema, MonsterAttackEventSchema
from shared.enums import ResultStatus
from shared.services.templates import TextTemplateServiceProtocol
from .subscriber import RedisSubscriberProtocol
from ..services.messages import MessageServiceProtocol
from ..schemas import MessageRequestSchema
from ..enums import MessageType
from ....core.db import AsyncSession, AsyncSessionFactory


logger = logging.getLogger(__name__)

class MiningEventHandlerProtocol(Protocol):
    async def handle_mining_finished(self, event_data: dict) -> Awaitable[None]: 
        ...

    async def start_listening(self) -> None:
        ...

    async def stop_listening(self) -> None:
        ...

class MiningEventHandler(MiningEventHandlerProtocol):
    def __init__(self, subscriber: RedisSubscriberProtocol, 
                message_service_factory: Callable[[AsyncSession], MessageServiceProtocol], 
                 template_service: TextTemplateServiceProtocol):
        self.subscriber = subscriber
        self.message_service_factory = message_service_factory
        self.template_service = template_service
        self._is_listening = False
    
    async def handle_mining_finished(self, event_data: dict) -> None:
        """Обработка события с валидацией и обработкой ошибок"""
        async with AsyncSessionFactory() as session:

            try:
                message_service = self.message_service_factory(session)
                mining_data = event_data["data"]
                
                # Валидация данных
                mining = MiningActionEventSchema.model_validate(mining_data)
                location = mining.location_slug.split('.')[-1]
                template_key = f"mining_locations_{location}_resources_{mining.result_status.value}"
                if mining.result_status == ResultStatus.SUCCESS:
                    params = {
                        "resource": mining.recived_resourse_name.capitalize(),
                        "amount": mining.count_recived_resource
                    }
                else:
                    params = {}

                content_message = self.template_service.get_template(template_key, **params)
                target_user_ids=[mining.character_id]
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
                    character_id=mining.character_id
                )
                monster_attack = mining.monster_attack
                if monster_attack:
                    monster_message = self._process_monster_attack(monster_attack, location, mining.character_id)
                    await message_service.create_message_direct(
                        message_type=MessageType.SYSTEM_PRIVATE,
                        room="system",
                        message=monster_message,
                        character_id=mining.character_id
                    )
                    if monster_attack.is_win:
                        monster_result_message = self._process_monster_attack_status(monster_attack, location, mining.character_id)
                        await message_service.create_message_direct(
                        message_type=MessageType.SYSTEM_PRIVATE,
                        room="system",
                        message=monster_result_message,
                        character_id=mining.character_id
                    )

            except ValidationError as e:
                logger.error(f"Validation error for mining data: {e}")
                logger.debug(f"Invalid data: {mining_data}")
                # Можно отправить событие об ошибке или обработать иначе
                
            except KeyError as e:
                logger.error(f"Missing key in event data: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error handling mining_finished: {e}")
                raise
    
    def _process_monster_attack(self, monster: MonsterAttackEventSchema, location: str, character_id: uuid.UUID) -> MessageRequestSchema:
        # Валидация данных
                template_key = f"mining_locations_{location}_monsters_attack"

                content_message = self.template_service.get_template(template_key)
                target_user_ids=[character_id]
                message = MessageRequestSchema(
                    content=content_message,
                    target_user_ids=target_user_ids,
                    is_trade=False,
                    is_private=False
                )
                return message
    
    def _process_monster_attack_status(self, monster: MonsterAttackEventSchema, location: str, character_id: uuid.UUID) -> MessageRequestSchema:
        status_monster = "standard" if monster.is_standart_monster else "improved"
        template_key = f"mining_locations_{location}_monsters_loot_{status_monster}"
        
        content_message = self.template_service.get_template(template_key)
        target_user_ids=[character_id]
        message = MessageRequestSchema(
                    content=content_message,
                    target_user_ids=target_user_ids,
                    is_trade=False,
                    is_private=False
                )
        return message
        



    async def start_listening(self) -> None:
        """Запуск прослушивания событий"""
        if self._is_listening:
            return
            
        await self.subscriber.subscribe("mining_finished", self._route_event)
        self._is_listening = True
        logger.info("Started listening for mining events")
    
    async def stop_listening(self) -> None:
        """Остановка прослушивания событий"""
        if not self._is_listening:
            return
            
        if hasattr(self.subscriber, 'stop'):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, 'unsubscribe'):
            await self.subscriber.unsubscribe("mining_finished")
            
        self._is_listening = False
        logger.info("Stopped listening for mining events")
    
    async def _route_event(self, event_data: dict) -> None:
        """Маршрутизация событий на соответствующие обработчики"""
        event_type = event_data.get("event_type")
        
        handlers = {
            "mining_finished": self.handle_mining_finished,
        }
        
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")