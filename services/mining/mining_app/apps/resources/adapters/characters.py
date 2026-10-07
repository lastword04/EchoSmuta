import uuid
from typing import Protocol, Self

from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import CharacterMiningStats, TirednessStat
from shared.schemas.errors import BaseResponseSchema

from ....core.adapters.base_http import BaseHttpClientImpl


class CharacterServiceClientProtocol(Protocol):
    async def get_simple_info_character(self: Self, character_id: uuid.UUID) -> CharacterMiningStats:
        """Получение простой информации о персонаже по ID"""
        ...

    async def update_tiredness(self, character_id: uuid.UUID, tiredness: float) -> StatusOkSchema:
        ...

class CharacterServiceClient(BaseHttpClientImpl, CharacterServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] | None = None
    ):
        if permissions is None:
            permissions = ["characters:read", "characters:write"]
        super().__init__(
            base_url=base_url,
            target_service="character-service", 
            permissions=permissions,
            timeout=timeout
        )
    
    async def get_simple_info_character(self: Self, character_id: uuid.UUID) -> CharacterMiningStats:
        return await self.request(
            "GET",
            f"/simple/info/{character_id}",
            response_model=CharacterMiningStats,
            error_model=BaseResponseSchema,
        )
    
    async def update_tiredness(self, character_id: uuid.UUID, tiredness: float) -> StatusOkSchema:
        stats = TirednessStat(tiredness=tiredness)
        return await self.request(
            "PUT",
            f"/{character_id}/tiredness",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )