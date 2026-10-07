from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.characters import (
    CharacterSimpleInfoListReadSchema,
    CharacterListIds,
    CharacterSimpleReadSchema
)
from ....core.adapters.base_http import BaseHttpClientImpl

class CharacterServiceClientProtocol(Protocol):
    async def get_simple_info_by_ids(self: Self, ids: CharacterListIds, is_online: Optional[bool] = None) -> CharacterSimpleInfoListReadSchema:
        """Получение краткой информации персонажей по IDs"""
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
    
    async def get_simple_info_by_ids(self: Self, ids: CharacterListIds, is_online: Optional[bool] = None) -> CharacterSimpleInfoListReadSchema:
        """Получение персонажа по ID"""
        params = {}
        if is_online is not None:
            params["is_online"] = str(is_online)

        return await self.request(
            "POST",
            "/simple/info/ids",
            json=ids.model_dump(mode='json'),
            params=params,
            response_model=CharacterSimpleInfoListReadSchema,
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