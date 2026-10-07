import sqlalchemy as sa
from sqlalchemy.orm import Session

from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import MonsterLocaton
from ..schemas import MonsterLocationReadSchema


class MonsterLocationSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_slug(self, slug: str) -> MonsterLocationReadSchema:
        stmt = sa.select(MonsterLocaton).where(MonsterLocaton.location_slug == slug)
        result = self.session.execute(stmt)
        instance = result.scalar_one_or_none()

        if not instance:
            raise ModelFieldNotFoundException(MonsterLocaton, 'location_slug', slug)

        return MonsterLocationReadSchema.model_validate(instance, from_attributes=True)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()