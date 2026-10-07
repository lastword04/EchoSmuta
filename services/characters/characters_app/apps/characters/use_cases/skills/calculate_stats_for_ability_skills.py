from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.character.characters import CharacterServiceProtocol
from ...schemas import ChangeSkillsRequest, ChangeSkillsResponse

class CalculateStatsForChangeUseCaseProtocol(UseCaseProtocol[ChangeSkillsResponse]):
    async def __call__(self, token: UserTokenDataReadSchema, data: ChangeSkillsRequest) -> ChangeSkillsResponse:
        ...
     

class CalculateStatsForChangeUseCase(CalculateStatsForChangeUseCaseProtocol):
    def __init__(self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self, token: UserTokenDataReadSchema, data: ChangeSkillsRequest) -> ChangeSkillsResponse:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.calculate_change_skills_cost(token.character_id, data)