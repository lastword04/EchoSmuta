import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.skills.applied_character_history import AppliedCharacterHistoryRepositoryProtocol
from ...schemas import (
    AppliedCharacterHistoryCreateSchema,
    AppliedCharacterHistoryUpdateSchema,
    AppliedCharacterHistoryUpdateDBSchema,
    AppliedCharacterHistoryReadSchema
)

class AppliedCharacterHistoryServiceProtocol(Protocol):
    repository: AppliedCharacterHistoryRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> AppliedCharacterHistoryReadSchema:
        ...

    async def create(self: Self, data: AppliedCharacterHistoryCreateSchema) -> AppliedCharacterHistoryReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: AppliedCharacterHistoryUpdateSchema) -> AppliedCharacterHistoryReadSchema:
        ...

    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> AppliedCharacterHistoryReadSchema:
        ...

    async def update_by_character_id(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryUpdateSchema) -> AppliedCharacterHistoryReadSchema:
        ...    

class AppliedCharacterHistoryService(AppliedCharacterHistoryServiceProtocol):
    def __init__(self: Self, repository: AppliedCharacterHistoryRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> AppliedCharacterHistoryReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: AppliedCharacterHistoryCreateSchema) -> AppliedCharacterHistoryReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, id: uuid.UUID, data: AppliedCharacterHistoryUpdateSchema) -> AppliedCharacterHistoryReadSchema:
        experience_character_settings_update_data = AppliedCharacterHistoryUpdateDBSchema(**data.model_dump(),
                                                               id=id
        )
        return await self.repository.update(experience_character_settings_update_data)
      
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> AppliedCharacterHistoryReadSchema:
        return await self.repository.get_by_character_id(character_id)
      
    async def update_by_character_id(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryUpdateSchema) -> AppliedCharacterHistoryReadSchema:
        return await self.repository.update_by_character_id(character_id, data)  