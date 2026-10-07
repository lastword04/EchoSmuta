import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.sessions import SessionUsersEventRepositoryProtocol
from ..schemas import (
    SessionUserEventRequestSchema,
    SessionUserEventCreateSchema,
    SessionUserEventReadSchema
)
from ..enums import EventType

class SessionUsersEventServiceProtocol(Protocol):
    async def create(self: Self, ip_address: str, request: SessionUserEventRequestSchema,
                     event_type: EventType, character_id: uuid.UUID) -> SessionUserEventReadSchema:
        ...

    async def bulk_create(
             self: Self, 
        ip_address: str, 
        request: SessionUserEventRequestSchema,
        event_type: EventType,
        character_ids: list[uuid.UUID]
    ) -> list[SessionUserEventReadSchema]:
        ...

class SessionUsersEventService(SessionUsersEventServiceProtocol):
    def __init__(self: Self, repository: SessionUsersEventRepositoryProtocol):
        self.repository = repository

    async def create(
        self: Self, 
        ip_address: str, 
        request: SessionUserEventRequestSchema,
        event_type: EventType,
        character_id: uuid.UUID
    ) -> SessionUserEventReadSchema:
        create_schema = SessionUserEventCreateSchema(
            ip_address=ip_address,
            fingerprint=request.fingerprint,
            event_type=event_type,
            character_id=character_id
        )
        return await self.repository.create(create_schema)

    async def bulk_create(
             self: Self, 
        ip_address: str, 
        request: SessionUserEventRequestSchema,
        event_type: EventType,
        character_ids: list[uuid.UUID]
    ) -> list[SessionUserEventReadSchema]:
        schemas = [
            SessionUserEventCreateSchema(
                ip_address=ip_address,
                fingerprint=request.fingerprint,
                event_type=event_type,
                character_id=character_id
            ) for character_id in character_ids
        ]
        return await self.repository.bulk_create(schemas)