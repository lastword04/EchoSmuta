import uuid
from typing_extensions import Self
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import WeightStat
from .....core.use_cases import UseCaseProtocol
from ...services.character.characters import UpdateCharacterWeightServiceProtocol


class UpdateCharacterWeightUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, character_id: uuid.UUID, stats: WeightStat) -> StatusOkSchema:
        ...


class UpdateCharacterWeightUseCase(UpdateCharacterWeightUseCaseProtocol):
    def __init__(self: Self, service: UpdateCharacterWeightServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID, stats: WeightStat) -> StatusOkSchema:
        await self.service.update_weight(character_id, stats.weight)
        return StatusOkSchema()
