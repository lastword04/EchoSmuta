import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

from ..models import CharacterResource, LocationResource, Resource
from ..schemas import LocationResourcePublic, LocationResourceWithAmount, ResourseCharacterResponse


class LocationResourcesCharacterSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_with_character_amounts(
        self, location_slug: str, character_id: uuid.UUID
    ) -> list[LocationResourceWithAmount]:
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

        result = self.session.execute(stmt)
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

    def get_all_by_location(self, location_slug: str) -> list[LocationResourcePublic]:
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

        result = self.session.execute(stmt)
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

    def get_all_my(self, character_id: uuid.UUID) -> list[ResourseCharacterResponse]:
        stmt = (
            sa.select(Resource.name, Resource.slug, CharacterResource.amount)
            .join(CharacterResource, Resource.slug == CharacterResource.resource_slug)
            .where(CharacterResource.character_id == character_id)
            .order_by(Resource.serial_number)
        )

        result = self.session.execute(stmt)
        rows = result.fetchall()

        return [
            ResourseCharacterResponse(
                resource_name=row.name,
                resource_slug=row.slug,
                amount=row.amount
            )
            for row in rows
        ]

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()