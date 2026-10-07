from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.character.characters import CharacterServiceProtocol
from ...schemas import AppliedCharacterHistoryCreateSchema
from shared.schemas.characters import CharacterReadSchema

class AddStatsToCharacterUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self, token: UserTokenDataReadSchema, data: AppliedCharacterHistoryCreateSchema) -> CharacterReadSchema:
        ...
     

class AddStatsToCharacterUseCase(AddStatsToCharacterUseCaseProtocol):
    def __init__(self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self, token: UserTokenDataReadSchema, data: AppliedCharacterHistoryCreateSchema) -> CharacterReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.add_stats_by_ability_skills(token.character_id, data)