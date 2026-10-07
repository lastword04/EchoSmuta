from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.locations import LocationReadSchema
from ....core.adapters.base_http import BaseHttpClientImpl

class LocationsServiceClientProtocol(Protocol):
    async def get_by_slug(self: Self, slug: str) -> LocationReadSchema:
        """Получение локации по slug"""
        ...


class LocationsServiceClient(BaseHttpClientImpl, LocationsServiceClientProtocol):
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
    
    async def get_by_slug(self: Self, slug: str) -> LocationReadSchema:
        """Получение персонажа по ID"""
        return await self.request(
            "GET",
            f"/locations/{slug}",
            response_model=LocationReadSchema,
            error_model=BaseResponseSchema
        )
    