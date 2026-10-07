import uuid

from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol
from ..models import House


class UpdateHouseWallpaperUseCaseProtocol(UseCaseProtocol[House]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID, wallpaper_photo_id: uuid.UUID | None) -> House:
        ...


class UpdateHouseWallpaperUseCase(UpdateHouseWallpaperUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID, wallpaper_photo_id: uuid.UUID | None) -> House:
        character = await self.character_repository.get(user.character_id)
        return await self.service.update_wallpaper(character, house_id, wallpaper_photo_id)