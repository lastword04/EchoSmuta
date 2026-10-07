from typing import Protocol, Self

from ..repositories.resources import ResourceRepositoryProtocol
from ..schemas import ResourceCreateSchema, ResourceReadSchema


class ResourceServiceProtocol(Protocol):
    async def get_by_slug(self: Self, slug: str) -> ResourceReadSchema:
        ...
    
    async def create(self: Self, resource: ResourceCreateSchema) -> ResourceReadSchema:
        ...

    async def bulk_create(self: Self, resources: list[ResourceCreateSchema]) -> list[ResourceReadSchema]:
        ...

    async def get_all(self: Self) -> list[ResourceReadSchema]:
        ...


class ResourceService(ResourceServiceProtocol):
    def __init__(self: Self, repository: ResourceRepositoryProtocol):
        self.repository = repository

    async def get_by_slug(self: Self, slug: str) -> ResourceReadSchema:
        return await self.repository.get_by_slug(slug)

    async def create(self: Self, resource: ResourceCreateSchema) -> ResourceReadSchema:
        return await self.repository.create(resource)

    async def bulk_create(self: Self, resources: list[ResourceCreateSchema]) -> list[ResourceReadSchema]:
        return await self.repository.bulk_create(resources)

    async def get_all(self: Self) -> list[ResourceReadSchema]:
        return await self.repository.get_all()