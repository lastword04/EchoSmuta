import uuid
from typing_extensions import Self

from ....core.use_cases import UseCaseProtocol
from ...characters.services.skills.reset_character_distributions import ResetCharacterDistributionsServiceProtocol


class ResetCharacterDistributionsUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, character_id: uuid.UUID) -> bool:
        ...


class ResetCharacterDistributionsUseCase(ResetCharacterDistributionsUseCaseProtocol):
    def __init__(self: Self, service: ResetCharacterDistributionsServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> bool:
        return await self.service.reset_character_distribution(character_id)
