import uuid
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import CraftingLicense, ShopNumberCounter


class CraftingLicenseRepositoryProtocol(Protocol):
    async def get_for_character(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicense | None: ...
    async def create(self, data: dict) -> CraftingLicense: ...
    async def update(self, license: CraftingLicense, end_date: datetime) -> CraftingLicense: ...

class CraftingLicenseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_character(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicense | None:
        stmt = select(CraftingLicense).where(
            CraftingLicense.character_id == character_id,
            CraftingLicense.location_slug == location_slug
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> CraftingLicense:
        license = CraftingLicense(**data)
        self.session.add(license)
        await self.session.commit()
        await self.session.refresh(license)
        return license

    async def update(self, license: CraftingLicense, end_date: datetime) -> CraftingLicense:
        license.end_date = end_date
        await self.session.commit()
        await self.session.refresh(license)
        return license

    async def get_next_number(self, location_slug: str) -> int:
        async with self.session as s:
            stmt = select(ShopNumberCounter).where(ShopNumberCounter.id == location_slug).with_for_update()
            result = await s.execute(stmt)
            counter = result.scalar_one_or_none()
            if not counter:
                counter = ShopNumberCounter(id=location_slug, last_number=0)
                s.add(counter)
            counter.last_number += 1
            await s.commit()
            return counter.last_number

