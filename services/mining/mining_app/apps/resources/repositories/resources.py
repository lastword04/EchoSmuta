from typing import Self

import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import Resource
from ..schemas import ResourceCreateSchema, ResourceReadSchema, ResourceUpdateSchema


class ResourceRepositoryProtocol(
    BaseRepositoryImpl[
        Resource,
        ResourceReadSchema,
        ResourceCreateSchema,
        ResourceUpdateSchema
    ]
):
    async def get_by_slug(self: Self, slug: str) -> ResourceReadSchema:
        ...

class ResourceRepository(ResourceRepositoryProtocol):
    async def get_by_slug(self: Self, slug: str) -> ResourceReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.slug == slug)
            )

            result = (await session.execute(stmt)).scalar_one_or_none()
            if not result:
                raise ModelFieldNotFoundException(self.model_type, 'slug', slug)
        
            return self.read_schema_type.model_validate(result, from_attributes=True)