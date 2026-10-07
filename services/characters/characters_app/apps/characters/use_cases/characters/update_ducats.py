import uuid
from typing_extensions import Self
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import DucatsStat
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import UpdateCharacterDucatsServiceProtocol 


class UpdateCharacterDucatsUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, character_id: uuid.UUID, stats: DucatsStat) -> StatusOkSchema:
        ...


class UpdateCharacterDucatsUseCase(UpdateCharacterDucatsUseCaseProtocol):
    def __init__(self: Self, service: UpdateCharacterDucatsServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID, stats: DucatsStat) -> StatusOkSchema:
        await self.service.update_ducats(character_id, stats.ducats)
        return StatusOkSchema()
