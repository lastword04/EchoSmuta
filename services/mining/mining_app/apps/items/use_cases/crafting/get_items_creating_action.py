import uuid
from typing import Protocol

from ...schemas import ItemsCreatingActionReadSchema
from ...services.crafting.items_creating_actions import (
    ItemsCreatingActionServiceProtocol,
)


class GetItemsCreatingActionUseCaseProtocol(Protocol):
    async def __call__(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        ...


class GetItemsCreatingActionUseCase(GetItemsCreatingActionUseCaseProtocol):
    def __init__(self, service: ItemsCreatingActionServiceProtocol):
        self.service = service

    async def __call__(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        return await self.service.get_for_character(action_id, character_id)
