import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.category import BaseCategoryStatsSchema
from shared.schemas.errors import BaseResponseSchema
from ....core.adapters.base_http import BaseHttpClientImpl

class CategoryServiceClientProtocol(Protocol):
    async def get_categories_stats(self: Self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        """Статистика категорий"""
        ...


class CategoryServiceClient(BaseHttpClientImpl, CategoryServiceClientProtocol):
    def __init__(
        self,
        base_url: str,
        timeout: float = 15.0,
        permissions: list[str] = ["chat:read", "chat:write"]
    ):
        super().__init__(
            base_url=base_url,
            target_service="chat-service",
            permissions=permissions,
            timeout=timeout
        )

    async def get_categories_stats(self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        """Статистика категорий"""


        return await self.request(
            "GET",
            f"/characters/{character_id}",
            response_model=BaseCategoryStatsSchema,
            error_model=BaseResponseSchema,
        )