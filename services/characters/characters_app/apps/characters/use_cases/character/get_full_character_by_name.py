from .....core.use_cases import UseCaseProtocol
from ...services.character.characters import GetFullInfoCharacterServiceProtocol
from ...schemas import CharacterFullInfoSchema

class GetFullCharacterByNameUseCaseProtocol(UseCaseProtocol[CharacterFullInfoSchema]):
    async def __call__(self, name: str) -> CharacterFullInfoSchema:
        ...

class GetFullCharacterByNameUseCase(GetFullCharacterByNameUseCaseProtocol):
    def __init__(self, service: GetFullInfoCharacterServiceProtocol):
        self.service = service

    async def __call__(self, name: str) -> CharacterFullInfoSchema:
        return await self.service.get_character_info_by_name(name)
