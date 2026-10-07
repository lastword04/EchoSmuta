from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.activity.activity import CharacterStatusChangerProtocol 


class ChangeStatusCharacterUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self) -> bool:
        ...


class ChangeStatusCharacterUseCase(ChangeStatusCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterStatusChangerProtocol):
        self.service = service

    async def __call__(self: Self) -> bool:
        return await self.service.change_status_for_inactive_characters()
