import uuid
from shared.schemas.characters import CharacterMiningStats
from .....core.use_cases import UseCaseProtocol
from ...services.characters_chat.characters_chat import CharacterChatServiceProtocol

class GetSimpleCharacterInfoUseCaseProtocol(UseCaseProtocol[CharacterMiningStats]):
    async def __call__(self, character_id: uuid.UUID) -> CharacterMiningStats:
        ...


class GetSimpleCharacterInfoUseCase(GetSimpleCharacterInfoUseCaseProtocol):
    def __init__(self, service: CharacterChatServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> CharacterMiningStats:
        return await self.service.get(character_id)