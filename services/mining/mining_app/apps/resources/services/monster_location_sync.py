from typing import Protocol

from ..models import MonsterLocaton
from ..repositories.monsters_location_sync import MonsterLocationSyncRepository
from ..schemas import MonsterLocationCreateSchema, MonsterLocationReadSchema


class MonsterLocationSyncServiceProtocol(Protocol):
    def get_by_slug(self, slug: str) -> MonsterLocationReadSchema: ...


class MonsterLocationSyncService(MonsterLocationSyncServiceProtocol):
    def __init__(self, repository: MonsterLocationSyncRepository):
        self.repository = repository

    def get_by_slug(self, slug: str) -> MonsterLocationReadSchema:
        return self.repository.get_by_slug(slug)

    def get_all(self) -> list[MonsterLocationReadSchema]:
        stmt = self.repository.session.query(MonsterLocaton).all()
        return [MonsterLocationReadSchema.model_validate(m, from_attributes=True) for m in stmt]

    def bulk_create(self, monsters: list[MonsterLocationCreateSchema]) -> list[MonsterLocationReadSchema]:
        models = [MonsterLocaton(**m.model_dump(exclude={'id'})) for m in monsters]
        self.repository.session.add_all(models)
        self.repository.session.flush()
        return [MonsterLocationReadSchema.model_validate(m, from_attributes=True) for m in models]