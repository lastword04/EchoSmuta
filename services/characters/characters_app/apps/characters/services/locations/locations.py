from typing import Protocol
from typing_extensions import Self
from shared.schemas.locations import LocationReadSchema
from ...repositories.locations.locations import LocationRepositoryProtocol
from ...schemas import LocationCreateSchema, LocationUpdateDBSchema


class LocationServiceProtocol(Protocol):
    async def get_by_slug(self: Self, slug: str) -> LocationReadSchema:
        ...
    
    async def create(self: Self, location: LocationCreateSchema) -> LocationReadSchema:
        ...
    
    async def update(self: Self, location_id: str, location: LocationUpdateDBSchema) -> LocationReadSchema:
        ...

    async def bulk_create(self: Self, locations: list[LocationCreateSchema]) -> list[LocationReadSchema]:
        ...

    async def get_all(self: Self) -> list[LocationReadSchema]:
        ...

class LocationService(LocationServiceProtocol):
    def __init__(self: Self, repository: LocationRepositoryProtocol):
        self.repository = repository

    async def get_by_slug(self: Self, slug: str) -> LocationReadSchema:
        return await self.repository.get_by_slug(slug)

    async def create(self: Self, location: LocationCreateSchema) -> LocationReadSchema:
        return await self.repository.create(location)

    async def update(self: Self, location_id: str, location: LocationUpdateDBSchema) -> LocationReadSchema:
        return await self.repository.update(location_id, location)
    
    async def bulk_create(self: Self, locations: list[LocationCreateSchema]) -> list[LocationReadSchema]:
        return await self.repository.bulk_create(locations)
    
    async def get_all(self: Self) -> list[LocationReadSchema]:
        return await self.repository.get_all()