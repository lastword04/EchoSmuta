from typing import Protocol

from ..models import LocationSettings
from ..repositories.location_settings_sync import LocationSettingsSyncRepository
from ..schemas import LocationSettingsCreateSchema, LocationSettingsReadSchema


class LocationSettingsSyncServiceProtocol(Protocol):
    def get_by_slug(self, slug: str) -> LocationSettingsReadSchema: ...


class LocationSettingsSyncService(LocationSettingsSyncServiceProtocol):
    def __init__(self, repository: LocationSettingsSyncRepository):
        self.repository = repository

    def get_by_slug(self, slug: str) -> LocationSettingsReadSchema:
        return self.repository.get_by_slug(slug)

    def get_all(self) -> list[LocationSettingsReadSchema]:
        stmt = self.repository.session.query(LocationSettings).all()
        return [LocationSettingsReadSchema.model_validate(m, from_attributes=True) for m in stmt]

    def bulk_create(self, settings: list[LocationSettingsCreateSchema]) -> list[LocationSettingsReadSchema]:
        models = [LocationSettings(**s.model_dump(exclude={'id'})) for s in settings]
        self.repository.session.add_all(models)
        self.repository.session.flush()
        return [LocationSettingsReadSchema.model_validate(m, from_attributes=True) for m in models]