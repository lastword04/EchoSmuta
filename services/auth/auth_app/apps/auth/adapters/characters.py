import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.characters import (
    CharacterCreateSchema,
    CharacterReadSchema,
    CharacterSimpleReadSchema,
    CharacterListIds
)
from ....core.adapters.base_http import BaseHttpClientImpl

class CharacterServiceClientProtocol(Protocol):
    async def create(self: Self, character: CharacterCreateSchema) -> CharacterReadSchema:
        """Создание нового персонажа"""
        ...

    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        """Получение персонажа по имени"""
        ...
        
    async def delete(self: Self, character_id: uuid.UUID) -> None:
        """Удаление персонажа по ID"""
        ...

    async def get_simple(self: Self, character_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение персонажа по ID"""
        ...

    async def get_simple_character_by_user(self: Self, users_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение главного персонажа по user ID"""
        ...

    async def play(self: Self, character_id: uuid.UUID, user_id: uuid.UUID) -> CharacterReadSchema:
        """Вход в игру"""
        ...

    async def play_main(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        """Вход в игру а главного персонажа"""
        ...

    async def quit(self: Self, character_id: uuid.UUID, user_id: uuid.UUID) -> CharacterReadSchema:
        """Выход из игры за конкретного персонажа"""
        ...
    
    async def quit_all(self: Self, user_id: uuid.UUID) -> CharacterListIds:
        """Выход за всех персонажей"""
        ...

class CharacterServiceClient(BaseHttpClientImpl, CharacterServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] = ["characters:read", "characters:write"] 
    ):
        super().__init__(
            base_url=base_url,
            target_service="character-service", 
            permissions=permissions,
            timeout=timeout
        )
    
    async def create(self: Self, character: CharacterCreateSchema) -> CharacterReadSchema:
        """Создание нового персонажа"""
        return await self.request(
            "POST",
            "/register",
            response_model=CharacterReadSchema,
            error_model=BaseResponseSchema,
            json=character.model_dump(mode='json'),
        )
    
    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        """Получение персонажа по имени"""
        return await self.request(
            "GET",
            f"/name/{name}",
            response_model=CharacterSimpleReadSchema,
            error_model=BaseResponseSchema
        )
    
    async def delete(self: Self, character_id: uuid.UUID) -> None:
        """Удаление персонажа по ID"""
        await self.request(
            "DELETE",
            f"/{character_id}",
            response_model=None,
            error_model=BaseResponseSchema,
        )
        return None

    async def get_simple(self: Self, character_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение персонажа по ID"""
        return await self.request(
            "GET",
            f"/simple/{character_id}",
            response_model=CharacterSimpleReadSchema,
            error_model=BaseResponseSchema
        )
    
    async def play(self: Self, character_id: uuid.UUID, user_id: uuid.UUID) -> CharacterReadSchema:
        """Вход в игру"""
        return await self.request(
            "POST",
            f"/{character_id}/user/{user_id}/play",
            response_model=CharacterReadSchema,
            error_model=BaseResponseSchema
        )
    
    async def play_main(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        """Вход в игру за основного персонажа"""
        return await self.request(
            "POST",
            f"/main/user/{user_id}/play",
            response_model=CharacterReadSchema,
            error_model=BaseResponseSchema
        )
    
    async def quit(self: Self, character_id: uuid.UUID, user_id: uuid.UUID) -> CharacterReadSchema:
        return await self.request(
            "POST",
            f"/{character_id}/user/{user_id}/quit",
            response_model=CharacterReadSchema,
            error_model=BaseResponseSchema
        )
    
    async def quit_all(self: Self, user_id: uuid.UUID) -> CharacterListIds:
        return await self.request(
            "POST",
            f"/all/user/{user_id}/quit",
            response_model=CharacterListIds,
            error_model=BaseResponseSchema
        )
    
    async def get_simple_character_by_user(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        return await self.request(
            "GET",
            f"/simple/user/{user_id}",
            response_model=CharacterSimpleReadSchema,
            error_model=BaseResponseSchema,
        )