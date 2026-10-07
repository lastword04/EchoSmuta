import uuid
from typing_extensions import Self
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import TirednessStat
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import UpdateCharacterTirednessServiceProtocol 


class UpdateCharacterTirednessUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, character_id: uuid.UUID, stats: TirednessStat) -> StatusOkSchema:
        ...


class UpdateCharacterTirednessUseCase(UpdateCharacterTirednessUseCaseProtocol):
    def __init__(self: Self, service: UpdateCharacterTirednessServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID, stats: TirednessStat) -> StatusOkSchema:
        await self.service.update_tiredness(character_id, stats.tiredness)
        return StatusOkSchema()
