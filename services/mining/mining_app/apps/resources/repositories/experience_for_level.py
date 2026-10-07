import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import ExperienceForLevel
from ..schemas import (
   ExperienceForLevelCreateSchema,
   ExperienceForLevelReadSchema,
   ExperienceForLevelUpdateSchema,
)


class ExperienceForLevelRepositoryProtocol(
    BaseRepositoryImpl[
        ExperienceForLevel,
        ExperienceForLevelReadSchema,
        ExperienceForLevelCreateSchema,
        ExperienceForLevelUpdateSchema
    ]
):
   async def get_current_level(
            self,
            current_level: int
    ) -> ExperienceForLevelReadSchema:
        ...

   async def get_current_and_next_level_experience(
        self,
        current_level: int
    ) -> tuple[ExperienceForLevelReadSchema | None, ExperienceForLevelReadSchema | None]:
        """
        Получает опыт для текущего и следующего уровней.
        Возвращает кортеж: (текущий уровень или None, следующий уровень или None).
        """

   async def get_next_level_experience(
        self,
        current_level: int
    ) -> ExperienceForLevelReadSchema | None:
        """
        Получает опыт, необходимый для следующего уровня после current_level.
        Если следующего уровня нет, возвращает None.
        """

    
class ExperienceForLevelRepository(ExperienceForLevelRepositoryProtocol):
    async def get_next_level_experience(
        self,
        current_level: int
    ) -> ExperienceForLevelReadSchema | None:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.level == current_level + 1)
            )

            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                return None

            return self.read_schema_type.model_validate(instance, from_attributes=True)
        
    async def get_current_and_next_level_experience(
        self,
        current_level: int
    ) -> tuple[ExperienceForLevelReadSchema | None, ExperienceForLevelReadSchema | None]:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    sa.or_(
                        self.model_type.level == current_level,
                        self.model_type.level == current_level + 1
                    )
                )
            )

            result = await session.execute(stmt)
            instances = result.scalars().all()

            current_instance = next((inst for inst in instances if inst.level == current_level), None)
            next_instance = next((inst for inst in instances if inst.level == current_level + 1), None)

            current_schema = (
                self.read_schema_type.model_validate(current_instance, from_attributes=True)
                if current_instance else None
            )
            next_schema = (
                self.read_schema_type.model_validate(next_instance, from_attributes=True)
                if next_instance else None
            )

            return current_schema, next_schema
        
    async def get_current_level(
            self,
            current_level: int
    ) -> ExperienceForLevelReadSchema:
         async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.level == current_level)
            )

            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                raise ModelFieldNotFoundException(self.model_type, "level", current_level)

            return self.read_schema_type.model_validate(instance, from_attributes=True)