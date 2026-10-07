import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.chat import ChatSettingsDefaultCreateSchema, ChatSettingsReadSchema
from ..repositories.settings import ChatSettingsRepositoryProtocol
from ..schemas import (
    ChatSettingsCreateSchema,
    ChatSettingsUpdateSchema,
    ChatSettingsUpdateDBSchema
)

class ChatSettingsServiceProtocol(Protocol):
    async def create_default(self: Self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        ...

    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> ChatSettingsReadSchema:
        ...

    async def update(self: Self, character_id: uuid.UUID, settings_id: uuid.UUID, settings: ChatSettingsUpdateSchema) -> ChatSettingsReadSchema:
        ...

class ChatSettingsService(ChatSettingsServiceProtocol):
    def __init__(self: Self, repository: ChatSettingsRepositoryProtocol):
        self.repository = repository

    async def create_default(self: Self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        return await self.repository.create(ChatSettingsCreateSchema(**data.model_dump()))
    
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> ChatSettingsReadSchema:
        return await self.repository.get_by_character_id(character_id)
    
    async def update(self: Self, character_id: uuid.UUID, settings_id: uuid.UUID, settings: ChatSettingsUpdateSchema) -> ChatSettingsReadSchema:
        schema_for_update = ChatSettingsUpdateDBSchema(
            id=settings_id,
            character_id=character_id,
            **settings.model_dump(exclude={"character_id", "id"})
            )
        return await self.repository.update_by_character_id(schema_for_update, character_id)
        
