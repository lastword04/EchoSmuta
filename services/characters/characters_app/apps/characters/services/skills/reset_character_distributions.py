import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.skills.character_distributions import CharacterDistributionsRepositoryProtocol
from ...schemas import (
    CharacterDistributionsCreateSchema,
    CharacterDistributionsUpdateSchema,
    CharacterDistributionsUpdateDBSchema,
    CharacterDistributionsReadSchema
)

class ResetCharacterDistributionsServiceProtocol(Protocol):
    repository: CharacterDistributionsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> CharacterDistributionsReadSchema:
        ...

    async def create(self: Self, data: CharacterDistributionsCreateSchema) -> CharacterDistributionsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: CharacterDistributionsUpdateSchema) -> CharacterDistributionsReadSchema:
        ...

    async def reset_character_distribution(self: Self, character_id: uuid.UUID) -> bool:
        ...

    
class ResetCharacterDistributionsService(ResetCharacterDistributionsServiceProtocol):
    def __init__(self: Self, repository: CharacterDistributionsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> CharacterDistributionsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: CharacterDistributionsCreateSchema) -> CharacterDistributionsReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, id: uuid.UUID, data: CharacterDistributionsUpdateSchema) -> CharacterDistributionsReadSchema:
        character_distributions_update_data = CharacterDistributionsUpdateDBSchema(**data.model_dump(exclude={'id'}),
                                                               id=id
        )
        return await self.repository.update(character_distributions_update_data)
      
    async def reset_character_distribution(self: Self, character_id: uuid.UUID) -> bool:
        return await self.repository.reset_character_distribution(character_id)
      
    