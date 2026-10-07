import uuid
from typing import Protocol, Self

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ...items.deals.enums import DealStatus, ResourceReservationStatus
from ...items.deals.models import Deal, DealResourceReservation
from ..models import CharacterResource, LocationResource, Resource
from ..schemas import LocationResourcePublic, LocationResourceWithAmount, ResourseCharacterResponse


class LocationResourcesCharacterRepositoryProtocol(Protocol):
    async def get_with_character_amounts(
        self,
        location_slug: str,
        character_id: uuid.UUID
    ) -> list[LocationResourceWithAmount]:
        ...

    async def get_all_by_location(
        self,
        location_slug: str
    ) -> list[LocationResourcePublic]:
        ...

    async def get_all_my(self: Self, character_id: uuid.UUID) -> list[ResourseCharacterResponse]:
        ...

class LocationResourcesCharacterRepository(LocationResourcesCharacterRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def get_with_character_amounts(
        self,
        location_slug: str,
        character_id: uuid.UUID
    ) -> list[LocationResourceWithAmount]:
        async with self.session as session:
            # Создаем алиасы для удобства
            lr = aliased(LocationResource)
            r = aliased(Resource)
            cr = aliased(CharacterResource)

            stmt = (
                sa.select(
                    r.name.label('resource_name'),
                    r.slug.label('resource_slug'),
                    lr.chance,
                    lr.current_amount,
                    sa.func.coalesce(cr.amount, 0).label('amount')
                )
                .join(r, lr.resource_slug == r.slug)
                .outerjoin(
                    cr,
                    (cr.character_id == character_id) & (cr.resource_slug == r.slug)
                )
                .where(lr.location_slug == location_slug)
                .order_by(r.serial_number)
            )

            result = await session.execute(stmt)
            rows = result.fetchall()

            return [
                LocationResourceWithAmount(
                    resource_name=row.resource_name,
                    resource_slug=row.resource_slug,
                    chance=row.chance,
                    current_amount=row.current_amount,
                    amount=row.amount
                )
                for row in rows
            ]
        
    async def get_all_by_location(
        self,
        location_slug: str
    ) -> list[LocationResourcePublic]:
        async with self.session as session:
            lr = aliased(LocationResource)
            r = aliased(Resource)

            stmt = (
                sa.select(
                    r.name.label('resource_name'),
                    r.slug.label('resource_slug'),
                    lr.chance,
                    lr.current_amount,
                    lr.experience_on_resource
                )
                .join(r, lr.resource_slug == r.slug)
                .where(lr.location_slug == location_slug)
                .order_by(lr.chance.desc())
            )

            result = await session.execute(stmt)
            rows = result.fetchall()

            return [
                LocationResourcePublic(
                    resource_name=row.resource_name,
                    resource_slug=row.resource_slug,
                    chance=row.chance,
                    current_amount=row.current_amount,
                    experience_on_resource=row.experience_on_resource
                )
                for row in rows
            ]
        
    async def get_all_my(self: Self, character_id: uuid.UUID) -> list[ResourseCharacterResponse]:
        async with self.session as session:
            # Сумма активных резерваций: status='ACTIVE' И сделка не финальная
            reserved_sum = sa.func.coalesce(
                sa.func.sum(
                    sa.case(
                        (
                            (DealResourceReservation.status == ResourceReservationStatus.ACTIVE)
                            & (Deal.status.in_([DealStatus.DRAFT, DealStatus.ACTIVE])),
                            DealResourceReservation.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("reserved")

            stmt = (
                sa.select(
                    Resource.name.label("resource_name"),
                    Resource.slug.label("resource_slug"),
                    CharacterResource.amount.label("amount"),
                    (CharacterResource.amount - reserved_sum).label("available_amount"),
                )
                .join(Resource, Resource.slug == CharacterResource.resource_slug)
                .outerjoin(
                    DealResourceReservation,
                    (DealResourceReservation.character_id == CharacterResource.character_id)
                    & (DealResourceReservation.resource_slug == CharacterResource.resource_slug),
                )
                .outerjoin(Deal, Deal.id == DealResourceReservation.deal_id)
                .where(CharacterResource.character_id == character_id)
                .where(CharacterResource.amount > 0)
                .group_by(Resource.name, Resource.slug, CharacterResource.amount, Resource.serial_number)
                .order_by(Resource.serial_number)
            )

            result = await session.execute(stmt)
            rows = result.fetchall()

            return [
                ResourseCharacterResponse(
                    resource_name=row.resource_name,
                    resource_slug=row.resource_slug,
                    amount=row.amount,
                    available_amount=row.available_amount,
                )
                for row in rows
            ]