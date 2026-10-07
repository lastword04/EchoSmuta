import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.economy.transfer_value_settings import TransferValueCharactersSettingsRepositoryProtocol
from ...schemas import (
    TransferValueCharactersSettingsCreateSchema, TransferValueCharactersSettingsUpdateSchema, 
    TransferValueCharactersSettingsUpdateDBSchema, TransferValueCharactersSettingsReadSchema
)

class TransferValueCharactersSettingsServiceProtocol(Protocol):
    repository: TransferValueCharactersSettingsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> TransferValueCharactersSettingsReadSchema:
        ...

    async def create(self: Self, settings: TransferValueCharactersSettingsCreateSchema) -> TransferValueCharactersSettingsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, settings: TransferValueCharactersSettingsUpdateSchema) -> TransferValueCharactersSettingsReadSchema:
        ...

    async def get_all(self: Self) -> list[TransferValueCharactersSettingsReadSchema]:
        ...


class TransferValueCharactersSettingsService(TransferValueCharactersSettingsServiceProtocol):
    def __init__(self, repository: TransferValueCharactersSettingsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> TransferValueCharactersSettingsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, settings: TransferValueCharactersSettingsCreateSchema) -> TransferValueCharactersSettingsReadSchema:
        return await self.repository.create(settings)

    async def update(self: Self, id: uuid.UUID, settings: TransferValueCharactersSettingsUpdateSchema) -> TransferValueCharactersSettingsReadSchema:
        db_settings = TransferValueCharactersSettingsUpdateDBSchema(
            id=id,
            **settings.model_dump()
        )
        return await self.repository.update(db_settings)

    async def get_all(self: Self) -> list[TransferValueCharactersSettingsReadSchema]:
        return await self.repository.get_all()