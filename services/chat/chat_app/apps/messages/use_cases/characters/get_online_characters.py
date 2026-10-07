from typing import Optional
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...adapter.characters import CharacterServiceClientProtocol
from ...services.ignore import IgnoreServiceProtocol
from ...schemas import CharacterOnlineReadSchema, CharacterOnlinePaginationSchema


class GetOnlineCharactersUseCaseProtocol(UseCaseProtocol[CharacterOnlinePaginationSchema]):
    async def __call__(
        self,
        limit: int,
        offset: int,
        token: UserTokenDataReadSchema,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> CharacterOnlinePaginationSchema:
        ...


class GetOnlineCharactersUseCase(GetOnlineCharactersUseCaseProtocol):
    def __init__(self, ignore_service: IgnoreServiceProtocol,
                 characters_service: CharacterServiceClientProtocol):
        self.ignore_service = ignore_service
        self.characters_service = characters_service

    async def __call__(
        self,
        limit: int,
        offset: int,
        token: UserTokenDataReadSchema,
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> CharacterOnlinePaginationSchema:
        characters = await self.characters_service.get_online_characters(
            limit, offset, location_slug, room_id
        )

        characters_ids = [character.id for character in characters.objects]
        ignored_characters = await self.ignore_service.get_ignored_characters(
            token.character_id, other_character_ids=characters_ids
        )
        characters_with_ignore_status = [
            CharacterOnlineReadSchema(
                **character.model_dump(),
                is_ignored=ignored_characters.get(character.id, False)
            )
            for character in characters.objects
        ]

        return CharacterOnlinePaginationSchema(
            objects=characters_with_ignore_status,
            count=characters.count
        )