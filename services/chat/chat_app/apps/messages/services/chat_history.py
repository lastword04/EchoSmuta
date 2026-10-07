import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from ..repositories.chat_history import ChatHistoryRepositoryProtocol
from ..schemas import MessagePaginationReadSchema


class ChatHistoryServiceProtocol(Protocol):
    async def get_chat_history(
        self: Self, 
        character_id: uuid.UUID, 
        room: str,
        location_slug: Optional[str],
        pagination: PaginationSchema
    ) -> MessagePaginationReadSchema:
        ...


class ChatHistoryService(ChatHistoryServiceProtocol):
    def __init__(self: Self, repository: ChatHistoryRepositoryProtocol):
        self.repository = repository

    async def get_chat_history(
        self: Self, 
        character_id: uuid.UUID, 
        room: str,
        location_slug: Optional[str],
        pagination: PaginationSchema
    ) -> MessagePaginationReadSchema:
        return await self.repository.get_chat_history(character_id, room, location_slug, pagination)