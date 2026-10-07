import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import MonsterLocaton
from ..schemas import (
    MonsterLocationCreateSchema,
    MonsterLocationReadSchema,
    MonsterLocationUpdateSchema,
)


class MonsterLocationRepositoryProtocol(
    BaseRepositoryImpl[
        MonsterLocaton,
        MonsterLocationReadSchema,
        MonsterLocationCreateSchema,
        MonsterLocationUpdateSchema
    ]
):
    async def get_by_slug(
        self,
        slug: str
    ) -> MonsterLocationReadSchema:
        """
        Получает настройки локации по её слагу.
        Если настройки не найдены, raise ModelFieldNotFoundException.
        """

class MonsterLocationRepository(MonsterLocationRepositoryProtocol):
    async def get_by_slug(
        self,
        slug: str
    ) -> MonsterLocationReadSchema:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(self.model_type.location_slug == slug)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                raise ModelFieldNotFoundException(self.model_type, 'location_slug', slug)

            return self.read_schema_type.model_validate(instance, from_attributes=True)