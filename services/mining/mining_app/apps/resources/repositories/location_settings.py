import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import LocationSettings
from ..schemas import (
    LocationSettingsCreateSchema,
    LocationSettingsReadSchema,
    LocationSettingsUpdateSchema,
)


class LocationSettingsRepositoryProtocol(
    BaseRepositoryImpl[
        LocationSettings,
        LocationSettingsReadSchema,
        LocationSettingsCreateSchema,
        LocationSettingsUpdateSchema
    ]
):
    async def get_by_slug(
        self,
        slug: str
    ) -> LocationSettingsReadSchema:
        """
        Получает настройки локации по её слагу.
        Если настройки не найдены, raise ModelFieldNotFoundException.
        """

class LocationSettingsRepository(LocationSettingsRepositoryProtocol):
    async def get_by_slug(
        self,
        slug: str
    ) -> LocationSettingsReadSchema:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(self.model_type.location_slug == slug)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                raise ModelFieldNotFoundException(LocationSettings, 'location_slug', slug)

            return self.read_schema_type.model_validate(instance, from_attributes=True)