from typing import Protocol, Self

from ..repositories.monsters_location import MonsterLocationRepositoryProtocol
from ..schemas import MonsterLocationCreateSchema, MonsterLocationReadSchema


class MonsterLocationServiceProtocol(Protocol):
    async def get_all(self: Self) -> list[MonsterLocationReadSchema]:
        ...

    async def bulk_create(self: Self, monsters: list[MonsterLocationCreateSchema]) -> list[MonsterLocationReadSchema]:
        ...

    async def get_by_slug(self: Self, slug: str) -> MonsterLocationReadSchema:
        ...

class MonsterLocationService(MonsterLocationServiceProtocol):
    def __init__(self: Self, repository: MonsterLocationRepositoryProtocol):
        self.repository = repository

    async def get_all(self: Self) -> list[MonsterLocationReadSchema]:
        return await self.repository.get_all()
    
    async def bulk_create(self: Self, monsters: list[MonsterLocationCreateSchema]) -> list[MonsterLocationReadSchema]:
        return await self.repository.bulk_create(monsters)
    
    async def get_by_slug(self: Self, slug: str) -> MonsterLocationReadSchema:
        return await self.repository.get_by_slug(slug)