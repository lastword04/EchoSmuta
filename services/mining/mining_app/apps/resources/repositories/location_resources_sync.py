import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..models import LocationResource


class LocationResourceSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def change_current_amount(
        self, location_slug: str, resource_slug: str, current_amount: int
    ) -> bool:
        stmt = (
            sa.update(LocationResource)
            .where(
                LocationResource.location_slug == location_slug,
                LocationResource.resource_slug == resource_slug
            )
            .values(current_amount=current_amount)
        )
        self.session.execute(stmt)
        return True

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()