import uuid
from typing import Protocol

from ...repositories.crafting.character_start_creating_item import (
    CharacterStartCreatingItemRepositoryProtocol,
)
from ...schemas import (
    CharacterStartCreatingItemCreateSchema,
    CharacterStartCreatingItemReadSchema,
)


class CharacterStartCreatingItemServiceProtocol(Protocol):
    async def create(
        self, data: CharacterStartCreatingItemCreateSchema
    ) -> CharacterStartCreatingItemReadSchema:
        ...

    async def update_craft_stage(
        self, start_creating_id: uuid.UUID, craft_stage: int
    ) -> CharacterStartCreatingItemReadSchema:
        ...

    async def get_all_by_character(
        self, character_id: uuid.UUID
    ) -> list[CharacterStartCreatingItemReadSchema]:
        ...


class CharacterStartCreatingItemService(CharacterStartCreatingItemServiceProtocol):
    def __init__(self, repository: CharacterStartCreatingItemRepositoryProtocol):
        self.repository = repository

    async def create(
        self, data: CharacterStartCreatingItemCreateSchema
    ) -> CharacterStartCreatingItemReadSchema:
        return await self.repository.create(data)

    async def update_craft_stage(
        self, start_creating_id: uuid.UUID, craft_stage: int
    ) -> CharacterStartCreatingItemReadSchema:
        return await self.repository.update_craft_stage(start_creating_id, craft_stage)

    async def get_all_by_character(
        self, character_id: uuid.UUID
    ) -> list[CharacterStartCreatingItemReadSchema]:
        return await self.repository.get_all_by_character(character_id)
