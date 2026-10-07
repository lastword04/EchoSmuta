import sqlalchemy as sa
from typing_extensions import Self
from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import City
from ...schemas import CityCreateSchema, CityUpdateDBSchema, CityReadSchema


class CityRepositoryProtocol(
    BaseRepositoryImpl[
        City,
        CityReadSchema,
        CityCreateSchema,
        CityUpdateDBSchema
    ]
):
    async def get_by_name(self: Self, name: str) -> CityReadSchema:
        ...

class CityRepository(CityRepositoryProtocol):
    async def get_by_name(self: Self, name: str) -> CityReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.name == name)
            )

            result = (await session.execute(stmt)).scalar_one_or_none()
            if not result:
                raise ModelFieldNotFoundException(self.model_type, 'name', name)
        
            return self.read_schema_type.model_validate(result, from_attributes=True)