import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from ...repositories.settings.user_character_settings import UserCharacterSettingsRepositoryProtocol
from ...models import UserCharacterSettings
from ...schemas import UserCharacterSettingsReadSchema, UserCharacterSettingsCreateSchema, UserCharacterSettingsUpdateSchema, UserCharacterSettingsUpdateDBSchema
from .....core.utils.exceptions import ModelFieldNotFoundException 

class UserCharacterSettingsServiceProtocol(Protocol):
    repository: UserCharacterSettingsRepositoryProtocol

    async def get_user_character_settings(self: Self, user_id: uuid.UUID) -> UserCharacterSettingsReadSchema:
        ...

    async def create_user_character_settings(self: Self, settings: UserCharacterSettingsCreateSchema) -> UserCharacterSettingsReadSchema:
        ...

    async def update_user_character_settings(self: Self, id: uuid.UUID, settings: UserCharacterSettingsUpdateSchema) -> UserCharacterSettingsReadSchema:
        ...

    async def get_by_user_id(self: Self, user_id: uuid.UUID) -> UserCharacterSettingsReadSchema:
        """Get user character settings by user ID."""
        ...

    async def get_by_user_id_or_none(self: Self, user_id: uuid.UUID) -> Optional[UserCharacterSettingsReadSchema]:
        """Get user character settings by user ID or None if not found."""
        ...

class UserCharacterSettingsService(UserCharacterSettingsServiceProtocol):
    def __init__(self, repository: UserCharacterSettingsRepositoryProtocol):
        self.repository = repository

    async def get_user_character_settings(self: Self, id: uuid.UUID) -> UserCharacterSettingsReadSchema:
        return await self.repository.get(id)

    async def create_user_character_settings(self: Self, settings: UserCharacterSettingsCreateSchema) -> UserCharacterSettingsReadSchema:
        return await self.repository.create(settings)

    async def update_user_character_settings(self: Self, id: uuid.UUID, settings: UserCharacterSettingsUpdateSchema) -> UserCharacterSettingsReadSchema:
        db_settings = UserCharacterSettingsUpdateDBSchema(
            id=id,
            **settings.model_dump()
        )
        return await self.repository.update(db_settings)

    async def get_by_user_id(self: Self, user_id: uuid.UUID) -> UserCharacterSettingsReadSchema:
        """Get user character settings by user ID."""
        settings = await self.repository.get_by_user_id(user_id)
        if settings is None:
            raise ModelFieldNotFoundException(UserCharacterSettings, "user_id", user_id)
        return settings
    
    async def get_by_user_id_or_none(self: Self, user_id: uuid.UUID) -> Optional[UserCharacterSettingsReadSchema]:
        return await self.repository.get_by_user_id(user_id)