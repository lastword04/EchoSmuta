from typing import Optional
from shared.schemas.characters import CharacterSimpleInfoListReadSchema, CharacterListIds
from .....core.use_cases import UseCaseProtocol
from ...services.characters_chat.characters_chat import CharacterChatServiceProtocol

class GetCharactersByIdsUseCaseProtocol(UseCaseProtocol[CharacterSimpleInfoListReadSchema]):
    async def __call__(self, characters_ids: CharacterListIds, is_online: Optional[bool] = None) -> CharacterSimpleInfoListReadSchema:
        ...


class GetCharactersByIdsUseCase(GetCharactersByIdsUseCaseProtocol):
    def __init__(self, service: CharacterChatServiceProtocol):
        self.service = service

    async def __call__(self, characters_ids: CharacterListIds, is_online: Optional[bool] = None) -> CharacterSimpleInfoListReadSchema:
        return await self.service.get_by_ids(characters_ids, is_online)