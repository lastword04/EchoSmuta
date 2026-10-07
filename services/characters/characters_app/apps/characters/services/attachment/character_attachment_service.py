import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.attachment.character_attachment_settings import CharacterAttachmentSettingsRepositoryProtocol
from ...schemas import (
    CharacterAttachmentSettingsCreateSchema, CharacterAttachmentSettingsUpdateSchema, 
    CharacterAttachmentSettingsUpdateDBSchema, CharacterAttachmentSettingsReadSchema
)

class CharacterAttachmentSettingsServiceProtocol(Protocol):
    repository: CharacterAttachmentSettingsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> CharacterAttachmentSettingsReadSchema:
        ...

    async def create(self: Self, settings: CharacterAttachmentSettingsCreateSchema) -> CharacterAttachmentSettingsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, settings: CharacterAttachmentSettingsUpdateSchema) -> CharacterAttachmentSettingsReadSchema:
        ...

    async def get_all(self: Self) -> list[CharacterAttachmentSettingsReadSchema]:
        ...


class CharacterAttachmentSettingsService(CharacterAttachmentSettingsServiceProtocol):
    def __init__(self, repository: CharacterAttachmentSettingsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> CharacterAttachmentSettingsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, settings: CharacterAttachmentSettingsCreateSchema) -> CharacterAttachmentSettingsReadSchema:
        return await self.repository.create(settings)

    async def update(self: Self, id: uuid.UUID, settings: CharacterAttachmentSettingsUpdateSchema) -> CharacterAttachmentSettingsReadSchema:
        db_settings = CharacterAttachmentSettingsUpdateDBSchema(
            id=id,
            **settings.model_dump()
        )
        return await self.repository.update(db_settings)

    async def get_all(self: Self) -> list[CharacterAttachmentSettingsReadSchema]:
        return await self.repository.get_all()