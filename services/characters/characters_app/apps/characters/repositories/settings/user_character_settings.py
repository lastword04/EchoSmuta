import uuid
import sqlalchemy as sa
from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import UserCharacterSettings
from ...schemas import UserCharacterSettingsReadSchema, UserCharacterSettingsCreateSchema, UserCharacterSettingsUpdateDBSchema


class UserCharacterSettingsRepositoryProtocol(BaseRepositoryImpl[
    UserCharacterSettings,
    UserCharacterSettingsReadSchema,
    UserCharacterSettingsCreateSchema,
    UserCharacterSettingsUpdateDBSchema
]):
    async def get_by_user_id(self, user_id: uuid.UUID) -> UserCharacterSettingsReadSchema:
        """Get user character settings by user ID."""
        ...
    


class UserCharacterSettingsRepository(UserCharacterSettingsRepositoryProtocol):
    async def get_by_user_id(self, user_id: uuid.UUID) -> UserCharacterSettingsReadSchema:
        """Get user character settings by user ID."""
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.user_id == user_id)
            )

            result = (await session.execute(stmt)).scalar_one_or_none()
            if result is None:
                return None

            return self.read_schema_type.model_validate(result, from_attributes=True)