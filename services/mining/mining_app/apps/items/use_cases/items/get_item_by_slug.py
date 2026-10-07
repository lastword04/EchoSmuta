from typing import Protocol

from ...schemas import ItemReadSchema
from ...services.items.items import ItemServiceProtocol


class GetItemBySlugUseCaseProtocol(Protocol):
    async def __call__(self, slug: str) -> ItemReadSchema:
        ...


class GetItemBySlugUseCase(GetItemBySlugUseCaseProtocol):
    def __init__(self, service: ItemServiceProtocol):
        self.service = service

    async def __call__(self, slug: str) -> ItemReadSchema:
        return await self.service.get_by_slug(slug)
