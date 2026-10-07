from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.skills.character_ability_skills import CharacterAbilitySkillsServiceProtocol
from ...schemas import CharacterAbilitySkillsReadSchema

class GetMyCharacterAbilitySkillsUseCaseProtocol(UseCaseProtocol[CharacterAbilitySkillsReadSchema]):
    async def __call__(self, token: UserTokenDataReadSchema) -> CharacterAbilitySkillsReadSchema:
        ...

class GetMyCharacterAbilitySkillsUseCase(GetMyCharacterAbilitySkillsUseCaseProtocol):
    def __init__(self, service: CharacterAbilitySkillsServiceProtocol):
        self.service = service

    async def __call__(self, token: UserTokenDataReadSchema) -> CharacterAbilitySkillsReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get_by_character_id(token.character_id)