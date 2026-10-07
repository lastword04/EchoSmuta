import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema, CharacterUpdateSchema
from ...characters.services.character.characters import GetMainCharacterByUserIdProtocol, UpdateCharacterProtocol

class GetMainCharacterAdapterProtocol(Protocol):
    async def get_main_character_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        ...

    async def get_character_by_id(self: Self, character_id: uuid.UUID) -> CharacterReadSchema:
        ...
        
class GetMainCharacterAdapter(GetMainCharacterAdapterProtocol):
    def __init__(self: Self, service: GetMainCharacterByUserIdProtocol) -> None:
        self.service = service

    async def get_main_character_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        return await self.service.get_main_character_by_user_id(user_id)
    
    async def get_character_by_id(self: Self, character_id: uuid.UUID) -> CharacterReadSchema:
        return await self.service.get_character_by_id(character_id)

class UpdateCharacterAdapterProtocol(Protocol):
    async def update_character(self: Self, character_id: uuid.UUID, data: CharacterUpdateSchema) -> CharacterReadSchema:
        ...

class UpdateCharacterAdapter(UpdateCharacterAdapterProtocol):
    def __init__(self: Self, service: UpdateCharacterProtocol) -> None:
        self.service = service

    async def update_character(self: Self, character_id: uuid.UUID, data: CharacterUpdateSchema) -> CharacterReadSchema:
        return await self.service.update_character(character_id, data)