import uuid
from typing import Protocol
from typing_extensions import Self
from ....core.utils.exceptions import ModelNotFoundException
from ..models import NewUsersVisit
from ..repositories.visits import NewUsersVisitRepositoryProtocol
from ..schemas import (
    NewUsersVisitCreateSchema, NewUsersVisitReadSchema, 
    NewUsersVisitRequestSchema
)

class NewUsersVisitServiceProtocol(Protocol):
    async def create(self: Self, ip_address: str, user_request: NewUsersVisitRequestSchema) -> NewUsersVisitReadSchema:
        ...

    async def register(self: Self, ip_address: str, fingerprint: str, refferal_name: str, user_visit_id: uuid.UUID, character_id: uuid.UUID) -> NewUsersVisitReadSchema:
        ...

class NewUsersVisitService(NewUsersVisitServiceProtocol):
    def __init__(self: Self, repository: NewUsersVisitRepositoryProtocol):
        self.repository = repository

    async def create(self: Self, ip_address: str, user_request: NewUsersVisitRequestSchema) -> NewUsersVisitReadSchema:
        schema_for_create = NewUsersVisitCreateSchema(
            ip_address=ip_address,
            fingerprint=user_request.fingerprint,
            refferal_name=user_request.refferal_name
        )
        model, _ = await self.repository.get_or_create(schema_for_create)
        return model

    async def register(self: Self, ip_address: str, fingerprint: str, refferal_name: str, user_visit_id: uuid.UUID, character_id: uuid.UUID) -> NewUsersVisitReadSchema:
        visit = await self.repository.get_by_ip(user_visit_id, ip_address)
        if not visit.character_id:
            return await self.repository.register(user_visit_id, character_id, refferal_name)
        else: 
            return await self.repository.create(
                NewUsersVisitCreateSchema(
                    ip_address=ip_address,
                    fingerprint=fingerprint,
                    refferal_name=refferal_name,
                    is_registered=True,
                    character_id=character_id
                )
            )