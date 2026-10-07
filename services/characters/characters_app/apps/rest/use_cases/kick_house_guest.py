import uuid

from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_guest_service import HouseGuestServiceProtocol


class KickHouseGuestUseCaseProtocol(UseCaseProtocol[dict]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, guest_character_id: uuid.UUID) -> dict:
        ...


class KickHouseGuestUseCase(KickHouseGuestUseCaseProtocol):
    def __init__(self: Self, service: HouseGuestServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema, guest_character_id: uuid.UUID) -> dict:
        character = await self.character_repository.get(user.character_id)
        return await self.service.kick_guest(character, guest_character_id)