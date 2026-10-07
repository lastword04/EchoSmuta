import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.info.characters_info import CharacterInfoRepositoryProtocol
from ...schemas import (
    CharacterInfoCreateSchema,
    CharacterInfoRequestSchema,
    CharacterInfoUpdateDBSchema,
    CharacterInfoReadSchema
) 

class CharacterInfoServiceProtocol(Protocol):
    async def create_default(self: Self, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        ...
    
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        ...

    async def update_by_character_id(self: Self, character_info_id: uuid.UUID,
                                     characters_update: CharacterInfoRequestSchema, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        ...

class CharacterInfoService(CharacterInfoServiceProtocol):
    def __init__(self: Self, repository: CharacterInfoRepositoryProtocol):
        self.repository = repository

    async def create_default(self: Self, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        create_schema = CharacterInfoCreateSchema(character_id=character_id)
        return await self.repository.create(create_schema)
    
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        return await self.repository.get_by_character_id(character_id)
    
    async def update_by_character_id(self: Self, character_info_id: uuid.UUID,
                                     characters_update: CharacterInfoRequestSchema, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        update_schema = CharacterInfoUpdateDBSchema(
            id=character_info_id,
            character_id=character_id,
            **characters_update.model_dump()
        )
        return await self.repository.update_by_character_id(update_schema, character_id)
        