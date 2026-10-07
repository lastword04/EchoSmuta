import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import Building
from ...schemas import BuildingBaseSchema, BuildingCreateSchema, BuildingReadSchema


class BuildingRepositoryProtocol(
    BaseRepositoryImpl[
        Building,
        BuildingReadSchema,
        BuildingCreateSchema,
        BuildingBaseSchema
    ]
):
    async def get_by_city_trading_location(self, city_trading_location_slug: str) -> BuildingReadSchema:
        """Get building by city trading location slug"""
    
    async def get_by_location_slug(self, location_slug: str) -> BuildingReadSchema | None:
        """Get building by location slug"""


class BuildingRepository(BuildingRepositoryProtocol):
    async def get_by_city_trading_location(self, city_trading_location_slug: str) -> BuildingReadSchema:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(
                self.model_type.city_trading_location_slug == city_trading_location_slug
            )
            result = (await session.execute(stmt)).scalar_one_or_none()
            
            if result is None:
                raise ModelFieldNotFoundException(
                    self.model_type,
                    'city_trading_location_slug',
                    city_trading_location_slug
                )
            
            return self.read_schema_type.model_validate(result, from_attributes=True)
    
    async def get_by_location_slug(self, location_slug: str) -> BuildingReadSchema | None:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(
                self.model_type.location_slug == location_slug
            )
            result = (await session.execute(stmt)).scalar_one_or_none()
            
            if result is None:
                return None
            
            return self.read_schema_type.model_validate(result, from_attributes=True)
