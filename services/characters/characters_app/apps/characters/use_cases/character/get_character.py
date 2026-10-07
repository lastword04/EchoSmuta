import uuid
from .....core.use_cases import UseCaseProtocol
from ...services.character.characters import GetFullInfoCharacterServiceProtocol
from ...schemas import CharacterFullInfoSchema

class GetCharacterUseCaseProtocol(UseCaseProtocol[CharacterFullInfoSchema]):
    async def __call__(self, character_id: uuid.UUID) -> CharacterFullInfoSchema:
        ...

class GetCharacterUseCase(GetCharacterUseCaseProtocol):
    def __init__(self, service: GetFullInfoCharacterServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> CharacterFullInfoSchema:
        return await self.service.get_character_info(character_id)
