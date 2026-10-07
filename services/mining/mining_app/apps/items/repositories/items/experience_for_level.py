
import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import ItemExperienceForLevel
from ...schemas import (
    ItemExperienceForLevelBaseSchema,
    ItemExperienceForLevelCreateSchema,
    ItemExperienceForLevelReadSchema,
)


class ItemExperienceForLevelRepositoryProtocol(
    BaseRepositoryImpl[
        ItemExperienceForLevel,
        ItemExperienceForLevelReadSchema,
        ItemExperienceForLevelCreateSchema,
        ItemExperienceForLevelBaseSchema
    ]
):
    async def get_current_level(self, current_level: int) -> ItemExperienceForLevelReadSchema:
        ...

    async def get_current_and_next_level_experience(
        self, current_level: int
    ) -> tuple[ItemExperienceForLevelReadSchema | None, ItemExperienceForLevelReadSchema | None]:
        ...

    async def get_next_level_experience(self, current_level: int) -> ItemExperienceForLevelReadSchema | None:
        ...


class ItemExperienceForLevelRepository(ItemExperienceForLevelRepositoryProtocol):
    async def get_current_level(self, current_level: int) -> ItemExperienceForLevelReadSchema:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(self.model_type.level == current_level)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if not instance:
                raise ModelFieldNotFoundException(self.model_type, "level", current_level)
            
            return self.read_schema_type.model_validate(instance, from_attributes=True)

    async def get_next_level_experience(self, current_level: int) -> ItemExperienceForLevelReadSchema | None:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(self.model_type.level == current_level + 1)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if not instance:
                return None
            
            return self.read_schema_type.model_validate(instance, from_attributes=True)

    async def get_current_and_next_level_experience(
        self, current_level: int
    ) -> tuple[ItemExperienceForLevelReadSchema | None, ItemExperienceForLevelReadSchema | None]:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(
                sa.or_(
                    self.model_type.level == current_level,
                    self.model_type.level == current_level + 1
                )
            )
            result = await session.execute(stmt)
            instances = result.scalars().all()

            current_instance = next((inst for inst in instances if inst.level == current_level), None)
            next_instance = next((inst for inst in instances if inst.level == current_level + 1), None)

            current_schema = self.read_schema_type.model_validate(current_instance, from_attributes=True) if current_instance else None
            next_schema = self.read_schema_type.model_validate(next_instance, from_attributes=True) if next_instance else None

            return current_schema, next_schema