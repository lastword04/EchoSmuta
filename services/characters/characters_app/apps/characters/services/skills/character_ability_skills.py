import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.skills.character_ability_skills import CharacterAbilitySkillsRepositoryProtocol
from ...schemas import (
    CharacterAbilitySkillsCreateSchema,
    CharacterAbilitySkillsUpdateSchema,
    CharacterAbilitySkillsUpdateDBSchema,
    CharacterAbilitySkillsReadSchema
)
 
class CharacterAbilitySkillsServiceProtocol(Protocol):
    repository: CharacterAbilitySkillsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> CharacterAbilitySkillsReadSchema:
        ...

    async def create(self: Self, data: CharacterAbilitySkillsCreateSchema) -> CharacterAbilitySkillsReadSchema:
        ...

    async def update(self: Self, data: CharacterAbilitySkillsUpdateSchema) -> CharacterAbilitySkillsReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def bulk_create(self: Self, data: list[CharacterAbilitySkillsCreateSchema]) -> list[CharacterAbilitySkillsReadSchema]:
       ...

    async def get_all(self: Self) -> list[CharacterAbilitySkillsReadSchema]:
        ...

    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterAbilitySkillsReadSchema:
        ...

class CharacterAbilitySkillsService(CharacterAbilitySkillsServiceProtocol):
    def __init__(self: Self, repository: CharacterAbilitySkillsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> CharacterAbilitySkillsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: CharacterAbilitySkillsCreateSchema) -> CharacterAbilitySkillsReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, data: CharacterAbilitySkillsUpdateSchema) -> CharacterAbilitySkillsReadSchema:
        return await self.repository.update(data)

    async def delete(self: Self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def bulk_create(self: Self, data: list[CharacterAbilitySkillsCreateSchema]) -> list[CharacterAbilitySkillsReadSchema]:
        return await self.repository.bulk_create(data)

    async def get_all(self: Self) -> list[CharacterAbilitySkillsReadSchema]:
        return await self.repository.get_all()
    
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterAbilitySkillsReadSchema:
        return await self.repository.get_by_character_id(character_id)
      