import uuid
from typing import Protocol
from typing_extensions import Self
from ...enums import CharacterSkillType
from ...repositories.skills.character_distributions import CharacterDistributionsRepositoryProtocol
from ...schemas import (
    CharacterDistributionsCreateSchema,
    CharacterDistributionsUpdateSchema,
    CharacterDistributionsUpdateDBSchema,
    CharacterDistributionsReadSchema
)

class CharacterDistributionsServiceProtocol(Protocol):
    repository: CharacterDistributionsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> CharacterDistributionsReadSchema:
        ...

    async def create(self: Self, data: CharacterDistributionsCreateSchema) -> CharacterDistributionsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: CharacterDistributionsUpdateSchema) -> CharacterDistributionsReadSchema:
        ...

    async def get_or_create_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterDistributionsReadSchema:
        ...

    async def get_by_character_id_and_skill_type(self: Self, character_id: uuid.UUID, skill_type: CharacterSkillType) -> CharacterDistributionsReadSchema:
        ...    

class CharacterDistributionsService(CharacterDistributionsServiceProtocol):
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
      
    async def get_or_create_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterDistributionsReadSchema:
        return await self.repository.get_or_create_by_character_id(character_id)
      
    async def get_by_character_id_and_skill_type(self: Self, character_id: uuid.UUID, skill_type: CharacterSkillType) -> CharacterDistributionsReadSchema:
        return await self.repository.get_by_character_id_and_skill_type(character_id, skill_type)  