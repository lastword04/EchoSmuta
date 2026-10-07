import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.characters import (
    CharacterSimpleReadSchema
)
from ....core.adapters.base_http import BaseHttpClientImpl

class CharacterServiceClientProtocol(Protocol):
    async def get_simple(self: Self, character_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение персонажа по ID"""
        ...
    
    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        """Получение персонажа по имени"""
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
    
    async def get_simple(self: Self, character_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение персонажа по ID"""
        return await self.request(
            "GET",
            f"/simple/{character_id}",
            response_model=CharacterSimpleReadSchema,
            error_model=BaseResponseSchema
        )
    
    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        """Получение персонажа по имени"""
        return await self.request(
            "GET",
            f"/name/{name}",
            response_model=CharacterSimpleReadSchema,
            error_model=BaseResponseSchema
        )