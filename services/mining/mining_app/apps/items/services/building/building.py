from typing import Protocol

from ...repositories.building.building import BuildingRepositoryProtocol
from ...schemas import BuildingCreateSchema, BuildingReadSchema


class BuildingServiceProtocol(Protocol):
    async def create(self, data: BuildingCreateSchema) -> BuildingReadSchema:
        ...

    async def get_all(self) -> list[BuildingReadSchema]:
        ...


class BuildingService(BuildingServiceProtocol):
    def __init__(self, repository: BuildingRepositoryProtocol):
        self.repository = repository

    async def create(self, data: BuildingCreateSchema) -> BuildingReadSchema:
        return await self.repository.create(data)

    async def get_all(self) -> list[BuildingReadSchema]:
        return await self.repository.get_all()
