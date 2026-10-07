from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.skills.character_distributions import CharacterDistributionsServiceProtocol
from ...services.skills.applied_character_history import AppliedCharacterHistoryServiceProtocol
from ...schemas import AllCharacterDistributionInfo

class AppliedCharacterHistoryUseCaseProtocol(UseCaseProtocol[AllCharacterDistributionInfo]):
    async def __call__(self, token: UserTokenDataReadSchema) -> AllCharacterDistributionInfo:
        ...

class AppliedCharacterHistoryUseCase(AppliedCharacterHistoryUseCaseProtocol):
    def __init__(self, service: AppliedCharacterHistoryServiceProtocol, new_service: CharacterDistributionsServiceProtocol):
        self.service = service
        self.new_service = new_service

    async def __call__(self, token: UserTokenDataReadSchema) -> AllCharacterDistributionInfo:
        if not token.character_id:
            raise PermissionDeniedError()
        history = await self.service.get_by_character_id(token.character_id)
        info = await self.new_service.get_or_create_by_character_id(token.character_id)
        result = AllCharacterDistributionInfo(history=history, info=info)    
        return result