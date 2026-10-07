from typing import Self

import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import LocationResource
from ..schemas import (
     LocationResourceCreateSchema,
     LocationResourceReadSchema,
     LocationResourceUpdateSchema,
)


class LocationResourceRepositoryProtocol(
    BaseRepositoryImpl[
        LocationResource,
        LocationResourceReadSchema,
        LocationResourceCreateSchema,
        LocationResourceUpdateSchema
    ]
):
     async def change_current_amount(self: Self, location_slug: str, resource_slug: str, current_amount: int) -> bool:
          ...

class LocationResourceRepository(LocationResourceRepositoryProtocol):
    async def change_current_amount(self: Self, location_slug: str, resource_slug: str, current_amount: int) -> bool:
         async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.location_slug == location_slug,
                        self.model_type.resource_slug == resource_slug
                        )
                .values(current_amount=current_amount)
            )

            await session.execute(stmt)

            return True

