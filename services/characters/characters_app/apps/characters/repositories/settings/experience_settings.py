from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import GlobalCharacterExperienceSettings
from typing_extensions import Self
from typing import Optional
from ...schemas import GlobalCharacterExperienceSettingsReadSchema, GlobalCharacterExperienceSettingsCreateSchema, GlobalCharacterExperienceSettingsUpdateSchema
import sqlalchemy as sa


class GlobalCharacterExperienceSettingsRepositoryProtocol(BaseRepositoryImpl[
    GlobalCharacterExperienceSettings,
    GlobalCharacterExperienceSettingsReadSchema,
    GlobalCharacterExperienceSettingsCreateSchema,
    GlobalCharacterExperienceSettingsUpdateSchema
]):
    async def find_by_level_and_max_experience(self: Self, level: int, experience: int) -> Optional[GlobalCharacterExperienceSettingsReadSchema]:
        ...

    async def find_all_by_level_and_max_experience(self: Self, level: int, experience: int) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        ...
    

class GlobalCharacterExperienceSettingsRepository(GlobalCharacterExperienceSettingsRepositoryProtocol):
    async def find_by_level_and_max_experience(self: Self, level: int, experience: int) -> Optional[GlobalCharacterExperienceSettingsReadSchema]:
        async with self.session as session:
            stmt = (
                sa.select(GlobalCharacterExperienceSettings)
                .where((GlobalCharacterExperienceSettings.level == level), (GlobalCharacterExperienceSettings.experience <= experience))
                .order_by(sa.desc(GlobalCharacterExperienceSettings.experience))
                .limit(1)
            )

            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            if instance:
                return self.read_schema_type.model_validate(instance, from_attributes=True)
            return None

    async def find_all_by_level_and_max_experience(self: Self, level: int, experience: int) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        async with self.session as session:
            stmt = (
                sa.select(GlobalCharacterExperienceSettings)
                .where((GlobalCharacterExperienceSettings.level <= level), (GlobalCharacterExperienceSettings.experience <= experience))
                .order_by(sa.desc(GlobalCharacterExperienceSettings.experience))
            )  # Убираем LIMIT, так как хотим получить ВСЕ подходящие записи

            result = await session.execute(stmt)
            instances = result.scalars().all()  # Получаем все экземпляры моделей

            # Преобразуем каждую модель в представление через read_schema_type
            schemas = [
                self.read_schema_type.model_validate(instance, from_attributes=True)
                for instance in instances
            ]

            return schemas

