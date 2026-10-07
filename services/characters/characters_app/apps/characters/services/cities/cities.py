from typing import Protocol
from typing_extensions import Self
from ...repositories.cities.cities import CityRepositoryProtocol
from ...schemas import CityReadSchema, CityCreateSchema


class CityServiceProtocol(Protocol):
    async def get_by_name(self: Self, name: str) -> CityReadSchema:
        ...
    
    async def create(self: Self, city: CityCreateSchema) -> CityReadSchema:
        ...

    async def bulk_create(self: Self, cities: list[CityCreateSchema]) -> list[CityReadSchema]:
        ...

    async def get_all(self: Self) -> list[CityReadSchema]:
        ...

class CityService(CityServiceProtocol):
    def __init__(self: Self, repository: CityRepositoryProtocol):
        self.repository = repository

    async def get_by_name(self: Self, name: str) -> CityReadSchema:
        return await self.repository.get_by_name(name)

    async def create(self: Self, city: CityCreateSchema) -> CityReadSchema:
        return await self.repository.create(city)

    async def bulk_create(self: Self, cities: list[CityCreateSchema]) -> list[CityReadSchema]:
        return await self.repository.bulk_create(cities)
    
    async def get_all(self: Self) -> list[CityReadSchema]:
        return await self.repository.get_all()