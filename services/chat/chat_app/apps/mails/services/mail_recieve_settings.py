import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from ..repositories.mail_recieve_settings import MailReceiveSettingsRepositoryProtocol
from ..schemas import MailRecieveSettingsReadSchema, MailRecieveSettingsCreateSchema

class MailReceiveSettingsServiceProtocol(Protocol):
    async def create_default(self: Self, character_id: uuid.UUID) -> MailRecieveSettingsReadSchema:
        ...

    async def get_by_character_or_none(self: Self, character_id: uuid.UUID) -> Optional[MailRecieveSettingsReadSchema]:
        ...

    async def delete_by_character_id(self: Self, character_id: uuid.UUID) -> bool:
        ...

class MailReceiveSettingsService(MailReceiveSettingsServiceProtocol):
    def __init__(self: Self, repository: MailReceiveSettingsRepositoryProtocol):
        self.repository = repository

    async def create_default(self: Self, character_id: uuid.UUID) -> MailRecieveSettingsReadSchema:
        settings_for_create = MailRecieveSettingsCreateSchema(
            character_id=character_id,
            is_block_send_mails=True
        )
        return await self.repository.create(settings_for_create)

    async def get_by_character_or_none(self: Self, character_id: uuid.UUID) -> Optional[MailRecieveSettingsReadSchema]:
        return await self.repository.get_by_character_or_none(character_id)

    async def delete_by_character_id(self: Self, character_id: uuid.UUID) -> bool:
        return await self.repository.delete_by_character_id(character_id)