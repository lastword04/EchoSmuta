import uuid
from typing import Protocol
from typing_extensions import Self
from ....apps.panels.schemas import CharacterFastItemReadSchema
from ....apps.panels.services.panels import ItemsCRUServiceProtocol

class CreateItemsAdapterProtocol(Protocol):
    async def create(self: Self, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        ...

class CreateItemsAdapter(CreateItemsAdapterProtocol):
    def __init__(self: Self, items_service: ItemsCRUServiceProtocol):
        self.items_service = items_service

    async def create(self: Self, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        return await self.items_service.create(character_id)