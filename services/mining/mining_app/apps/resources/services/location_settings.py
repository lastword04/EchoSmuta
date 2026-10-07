from typing import Protocol

from ..repositories.location_settings import LocationSettingsRepositoryProtocol
from ..schemas import LocationSettingsCreateSchema, LocationSettingsReadSchema


class LocationSettingsServiceProtocol(Protocol):
    async def get_all(self) -> list[LocationSettingsReadSchema]:
        ...

    async def bulk_create(self, settings: list[LocationSettingsCreateSchema]) -> list[LocationSettingsReadSchema]:
        ...

    async def get_by_slug(self, slug: str) -> LocationSettingsReadSchema:
        ...

class LocationSettingsService(LocationSettingsServiceProtocol):
    def __init__(
        self,
        repository: LocationSettingsRepositoryProtocol
    ):
        self.repository = repository

    async def get_all(self) -> list[LocationSettingsReadSchema]:
        return await self.repository.get_all()

    async def bulk_create(self, settings: list[LocationSettingsCreateSchema]) -> list[LocationSettingsReadSchema]:
        return await self.repository.bulk_create(settings)
    
    async def get_by_slug(self, slug: str) -> LocationSettingsReadSchema:
        return await self.repository.get_by_slug(slug)