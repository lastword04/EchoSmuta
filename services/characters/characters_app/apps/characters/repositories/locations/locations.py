import sqlalchemy as sa
import uuid
from typing_extensions import Self
from shared.schemas.locations import LocationReadSchema
from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import Location, Character
from ...schemas import LocationCreateSchema, LocationUpdateDBSchema


class LocationRepositoryProtocol(
    BaseRepositoryImpl[
        Location,
        LocationReadSchema,
        LocationCreateSchema,
        LocationUpdateDBSchema
    ]
):
    async def get_by_slug(self: Self, slug: str) -> LocationReadSchema:
        ...

    async def exist_or_raise(self: Self, slug: str) -> None:
        """Проверяет существование Location по slug, вызывает исключение, если не найден."""
        ...

    async def get_location_for_character(self: Self, character_id: uuid.UUID) -> LocationReadSchema:
        ...

class LocationRepository(LocationRepositoryProtocol):
    async def get_by_slug(self: Self, slug: str) -> LocationReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.slug == slug)
            )

            result = (await session.execute(stmt)).scalar_one_or_none()
            if not result:
                raise ModelFieldNotFoundException(self.model_type, 'slug', slug)
        
            return self.read_schema_type.model_validate(result, from_attributes=True)
        
    async def exist_or_raise(self: Self, slug: str) -> None:
        async with self.session as session:
            stmt = (
                sa.select(sa.exists().where(self.model_type.slug == slug))
            )

            exists = (await session.execute(stmt)).scalar()
            if not exists:
                raise ModelFieldNotFoundException(self.model_type, 'slug', slug)
            
    async def get_location_for_character(self: Self, character_id: uuid.UUID) -> LocationReadSchema:
        """
        Получает локацию для персонажа одним запросом.
        """
        
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .join(Character, Character.location_slug == Location.slug)
                .where(Character.id == character_id)
                .where(Character.is_active == True)
            )
            
            result = (await session.execute(stmt)).scalar_one_or_none()
            if result is None:
                raise ModelFieldNotFoundException(Location, 'character_id', character_id)
            
            return LocationReadSchema.model_validate(result, from_attributes=True)