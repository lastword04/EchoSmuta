import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.characters import CharacterListIds
from ...repositories.characters_chat.characters_chat import CharacterChatRepositoryProtocol
from shared.schemas.base import PaginationSchema
from shared.schemas.characters import (
    PaginationCharacterSimpleInfoReadSchema, CharacterSimpleInfoListReadSchema,
    CharacterMiningStats,
)

class CharacterChatServiceProtocol(Protocol):
    async def paginate_online_active(
        self: Self,
        pagination: PaginationSchema,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> PaginationCharacterSimpleInfoReadSchema:
        ...

    async def get_by_ids(self: Self, character_ids: CharacterListIds, is_online: Optional[bool] = None) -> CharacterSimpleInfoListReadSchema:
        ...

    async def get(self: Self, character_id: str) -> CharacterMiningStats:
        ...

class CharacterChatService(CharacterChatServiceProtocol):
    def __init__(self: Self, repository: CharacterChatRepositoryProtocol):
        self.repository = repository

    async def paginate_online_active(
        self: Self,
        pagination: PaginationSchema,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> PaginationCharacterSimpleInfoReadSchema:
        characters = await self.repository.paginate_online_active(
            search=None,
            search_by=[],
            sorting=["name"],
            pagination=pagination,
            user=None,
            policies=["can_view"],
            location_slug=location_slug,
            room_id=room_id,
        )
        return characters
    
    async def get_by_ids(self: Self, character_ids: CharacterListIds, is_online: Optional[bool] = None) -> CharacterSimpleInfoListReadSchema:
        characters = await self.repository.get_by_ids(character_ids.ids, is_online=is_online)
        return CharacterSimpleInfoListReadSchema(
            characters=characters
        )
    
    async def get(self: Self, character_id: uuid.UUID) -> CharacterMiningStats:
        return await self.repository.get(character_id)