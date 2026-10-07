from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 
from ....stats.services.effective_stats import EffectiveStatsService
from ..valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class GetMeUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterReadSchema:
        ...


class GetMeUseCase(GetMeUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol,
                 effective_stats: EffectiveStatsService):
        self.service = service
        self.valid_or_raise = valid_or_raise
        self.effective_stats = effective_stats

    async def __call__(self: Self, token: UserTokenDataReadSchema,
                       ) -> CharacterReadSchema:
        await self.valid_or_raise(token)
        character = await self.service.get(token.character_id)

        effective = await self.effective_stats.calculate(character)
        for key, value in effective.items():
            setattr(character, key, value)

        return character
