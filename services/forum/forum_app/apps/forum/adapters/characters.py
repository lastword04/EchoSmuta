import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.characters import (
    CharacterSimpleReadSchema,
    UserListids,
    CharacterSimpleListReadSchema
)
from ....core.adapters.base_http import BaseHttpClientImpl

class CharacterServiceClientProtocol(Protocol):
    async def get_list_simple_characters_by_users(self: Self, users_ids: UserListids) -> CharacterSimpleListReadSchema:
        """Получение главных персонажей по user ID"""
        ...

    async def get_simple_character_by_user(self: Self, users_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение главного персонажа по user ID"""
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
    
    async def get_list_simple_characters_by_users(self: Self, users_ids: UserListids) -> CharacterSimpleListReadSchema:
        """Получение персонажей по ID"""
        return await self.request(
            "POST",
            "/simple/users/",
            response_model=CharacterSimpleListReadSchema,
            error_model=BaseResponseSchema,
            json=users_ids.model_dump(mode='json'),
        )
    
    async def get_simple_character_by_user(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        return await self.request(
            "GET",
            f"/simple/user/{user_id}",
            response_model=CharacterSimpleReadSchema,
            error_model=BaseResponseSchema,
        )