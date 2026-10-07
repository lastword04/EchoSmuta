import sqlalchemy as sa
from sqlalchemy.orm import Session

from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import LocationSettings
from ..schemas import LocationSettingsReadSchema


class LocationSettingsSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_slug(self, slug: str) -> LocationSettingsReadSchema:
        stmt = sa.select(LocationSettings).where(LocationSettings.location_slug == slug)
        result = self.session.execute(stmt)
        instance = result.scalar_one_or_none()

        if not instance:
            raise ModelFieldNotFoundException(LocationSettings, 'location_slug', slug)

        return LocationSettingsReadSchema.model_validate(instance, from_attributes=True)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()