from typing import Optional
from shared.schemas.base import PaginationSchema
from shared.schemas.characters import PaginationCharacterSimpleInfoReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.characters_chat.characters_chat import CharacterChatServiceProtocol

class GetOnlineCharactersUseCaseProtocol(UseCaseProtocol[PaginationCharacterSimpleInfoReadSchema]):
    async def __call__(
        self,
        limit: int,
        offset: int,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ):
        ...


class GetOnlineCharactersUseCase(GetOnlineCharactersUseCaseProtocol):
    def __init__(self, service: CharacterChatServiceProtocol):
        self.service = service

    async def __call__(
        self,
        limit: int,
        offset: int,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ):
        pagination = PaginationSchema(limit=limit, offset=offset)
        return await self.service.paginate_online_active(
            pagination=pagination,
            location_slug=location_slug,
            room_id=room_id,
        )