import uuid
from typing import Protocol

from ...schemas import ItemsCreatingActionResponseSchema
from ...services.crafting.items_creating_actions import (
    ItemsCreatingActionServiceProtocol,
)


class GetCraftingStatusUseCaseProtocol(Protocol):
    async def __call__(self, character_id: uuid.UUID) -> ItemsCreatingActionResponseSchema:
        ...


class GetCraftingStatusUseCase(GetCraftingStatusUseCaseProtocol):
    def __init__(self, service: ItemsCreatingActionServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> ItemsCreatingActionResponseSchema:
        return await self.service.get_processing_creating_action(character_id)
