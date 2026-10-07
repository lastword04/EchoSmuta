import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Protocol

from pydantic import ValidationError

from shared.enums import LocationType
from shared.schemas.characters import CharacterChangeLocationEvent

from .....core.db import AsyncSession, AsyncSessionFactory
from ...services.mining_actions import CancelMiningProcessServiceProtocol
from .subscriber import RedisSubscriberProtocol

logger = logging.getLogger(__name__)

class MiningEventHandlerProtocol(Protocol):
    async def handle_character_change_location(self, event_data: dict) -> Awaitable[None]: 
        ...

    async def handle_character_quit(self, event_data: dict) -> Awaitable[None]: 
        ...

    async def handle_quit(self, event_data: dict) -> Awaitable[None]: 
        ...

    async def start_listening(self) -> None:
        ...

    async def stop_listening(self) -> None:
        ...

class MiningEventHandler(MiningEventHandlerProtocol):
    def __init__(self, subscriber: RedisSubscriberProtocol, 
                mining_service_factory: Callable[[AsyncSession], CancelMiningProcessServiceProtocol]):
        self.subscriber = subscriber
        self.mining_service_factory = mining_service_factory
        self._is_listening = False
    
    async def handle_character_change_location(self, event_data: dict) -> Awaitable[None]:
        """Обработка события с валидацией и обработкой ошибок"""
        async with AsyncSessionFactory() as session:
            try:
                mining_service = self.mining_service_factory(session)
                location_data = event_data["data"]
                
                # Валидация данных
                location = CharacterChangeLocationEvent.model_validate(location_data)
                if location.old_location.type == LocationType.RESOURCES:
                    await mining_service.cancel_mining(location.character_id)


            except ValidationError as e:
                logger.error(f"Validation error for location data: {e}")
                logger.debug(f"Invalid data: {location}")
                # Можно отправить событие об ошибке или обработать иначе
                
            except KeyError as e:
                logger.error(f"Missing key in event data: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error handling change_location: {e}")
                raise  

    async def handle_character_quit(self, event_data: dict) -> Awaitable[None]: 
        async with AsyncSessionFactory() as session:
            try:
                mining_service = self.mining_service_factory(session)
                character_id = uuid.UUID(event_data["data"])
                
                await mining_service.cancel_mining(character_id)


            except ValidationError as e:
                logger.error(f"Validation error for quit character: {e}")
                logger.debug(f"Invalid data: {character_id}")
                # Можно отправить событие об ошибке или обработать иначе
                
            except KeyError as e:
                logger.error(f"Missing key in event data: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error handling change_location: {e}")
                raise 

    async def start_listening(self) -> None:
        """Запуск прослушивания событий"""
        if self._is_listening:
            return
            
        await self.subscriber.subscribe("change_location", self._route_event)
        self._is_listening = True
        logger.info("Started listening for mining events")
    
    async def stop_listening(self) -> None:
        """Остановка прослушивания событий"""
        if not self._is_listening:
            return
            
        if hasattr(self.subscriber, 'stop'):
            await self.subscriber.stop()
        elif hasattr(self.subscriber, 'unsubscribe'):
            await self.subscriber.unsubscribe("change_location")
            
        self._is_listening = False
        logger.info("Stopped listening for mining events")
    
    async def _route_event(self, event_data: dict) -> None:
        """Маршрутизация событий на соответствующие обработчики"""
        event_type = event_data.get("event_type")
        
        handlers = {
            "change_location": self.handle_character_change_location,
            "quit": self.handle_character_quit
        }
        
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")