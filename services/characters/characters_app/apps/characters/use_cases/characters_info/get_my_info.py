from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.info.characters_info import CharacterInfoServiceProtocol
from ...schemas import CharacterInfoReadSchema

class GetMyCharactersInfoUseCaseProtocol(UseCaseProtocol[CharacterInfoReadSchema]):
    async def __call__(self, token: UserTokenDataReadSchema) -> CharacterInfoReadSchema:
        ...

class GetMyCharacterInfoUseCase(GetMyCharactersInfoUseCaseProtocol):
    def __init__(self, service: CharacterInfoServiceProtocol):
        self.service = service

    async def __call__(self, token: UserTokenDataReadSchema) -> CharacterInfoReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get_by_character_id(token.character_id)