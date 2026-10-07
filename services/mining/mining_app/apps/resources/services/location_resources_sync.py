from typing import Protocol

from ..models import LocationResource
from ..repositories.location_resources_sync import LocationResourceSyncRepository
from ..schemas import LocationResourceCreateSchema, LocationResourceReadSchema


class LocationResourceSyncServiceProtocol(Protocol):
    def change_current_amount(self, location_slug: str, resource_slug: str, current_amount: int) -> None: ...


class LocationResourceSyncService(LocationResourceSyncServiceProtocol):
    def __init__(self, repository: LocationResourceSyncRepository):
        self.repository = repository

    def change_current_amount(self, location_slug: str, resource_slug: str, current_amount: int) -> None:
        self.repository.change_current_amount(location_slug, resource_slug, current_amount)

    def get_all(self) -> list[LocationResourceReadSchema]:
        stmt = self.repository.session.query(LocationResource).all()
        return [LocationResourceReadSchema.model_validate(m, from_attributes=True) for m in stmt]

    def bulk_create(self, resources: list[LocationResourceCreateSchema]) -> list[LocationResourceReadSchema]:
        models = [LocationResource(**r.model_dump(exclude={'id'})) for r in resources]
        self.repository.session.add_all(models)
        self.repository.session.flush()
        return [LocationResourceReadSchema.model_validate(m, from_attributes=True) for m in models]