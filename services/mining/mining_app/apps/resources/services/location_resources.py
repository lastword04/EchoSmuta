from typing import Protocol, Self

from ..repositories.location_resources import LocationResourceRepositoryProtocol
from ..schemas import LocationResourceCreateSchema, LocationResourceReadSchema


class LocationResourceServiceProtocol(Protocol):
    async def create(self: Self, resource: LocationResourceCreateSchema) -> LocationResourceReadSchema:
        ...

    async def bulk_create(self: Self, resources: list[LocationResourceCreateSchema]) -> list[LocationResourceReadSchema]:
        ...

    async def get_all(self: Self) -> list[LocationResourceReadSchema]:
        ...

    async def change_current_amount(self: Self, location_slug: str, resource_slug: str, current_amount: int) -> None:
        ...


class LocationResourceService(LocationResourceServiceProtocol):
    def __init__(self: Self, repository: LocationResourceRepositoryProtocol):
        self.repository = repository

    async def create(self: Self, resource: LocationResourceCreateSchema) -> LocationResourceReadSchema:
        return await self.repository.create(resource)

    async def bulk_create(self: Self, resources: list[LocationResourceCreateSchema]) -> list[LocationResourceReadSchema]:
        return await self.repository.bulk_create(resources)

    async def get_all(self: Self) -> list[LocationResourceReadSchema]:
        return await self.repository.get_all()
    
    async def change_current_amount(self: Self, location_slug: str, resource_slug: str, current_amount: int) -> None:
        await self.repository.change_current_amount(location_slug, resource_slug, current_amount)