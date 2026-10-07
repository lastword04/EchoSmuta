import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.characters import (
    CharacterSimpleReadSchema,
    CharacterSimpleListReadSchema,
    CharacterListIds,
    PaginationCharacterSimpleInfoReadSchema,
    CharacterOnlineStatus,
    CharacterIdsResponse,
)
from ....core.adapters.base_http import BaseHttpClientImpl

class CharacterServiceClientProtocol(Protocol):
    async def get_simple(self: Self, character_id: uuid.UUID) -> CharacterSimpleReadSchema:
        """Получение персонажа по ID"""
        ...
        
    async def get_list_simple_characters_by_ids(self: Self, characters_ids: CharacterListIds) -> CharacterSimpleListReadSchema:
        """Получение всех персонажей по их ID"""
        ...

    async def get_character_ids_by_location(self: Self, location_slug: str) -> list[uuid.UUID]:
        """Получить список ID всех персонажей в локации"""
        ...    

    async def get_online_characters(self: Self, limit: int, offset: int, location_slug: Optional[str] = None, room_id: Optional[str] = None) -> PaginationCharacterSimpleInfoReadSchema:
        ...

    async def get_online_status_character(self: Self, character_id: uuid.UUID) -> CharacterOnlineStatus:
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
    
    async def get_list_simple_characters_by_ids(self: Self, characters_ids: CharacterListIds) -> CharacterSimpleListReadSchema:
        """Получение персонажей по ID"""
        return await self.request(
            "POST",
            "/simple/ids",
            response_model=CharacterSimpleListReadSchema,
            error_model=BaseResponseSchema,
            json=characters_ids.model_dump(mode='json'),
        )

    async def get_character_ids_by_location(self: Self, location_slug: str) -> list[uuid.UUID]:
        """Получить список ID всех персонажей в локации"""
        response = await self.request(
            "GET",
            f"/by-location/{location_slug}",
            response_model=CharacterIdsResponse,
            error_model=BaseResponseSchema
        )
        return response.ids
    
    async def get_online_characters(
        self: Self,
        limit: int,
        offset: int,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> PaginationCharacterSimpleInfoReadSchema:
        params = {
            "limit": limit,
            "offset": offset,
        }
        if location_slug is not None:
            params["location_slug"] = location_slug
        if room_id is not None:
            params["room_id"] = room_id    

        return await self.request(
            "GET",
            "/online",
            response_model=PaginationCharacterSimpleInfoReadSchema,
            error_model=BaseResponseSchema,
            params=params
        )
    
    async def get_online_status_character(self: Self, character_id: uuid.UUID) -> CharacterOnlineStatus:
        return await self.request(
            "GET",
            f"/{character_id}/is-online",
            response_model=CharacterOnlineStatus,
            error_model=BaseResponseSchema
        )