from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol
from ...schemas import CategoryWithCharacterCountSchema
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class GetMyWithCountsCategoriesUseCaseProtocol(UseCaseProtocol[list[CategoryWithCharacterCountSchema]]):
    async def __call__(self, token: UserTokenDataReadSchema) -> list[CategoryWithCharacterCountSchema]:
        ...

class GetMyWithCountsCategoriesUseCase(GetMyWithCountsCategoriesUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, token: UserTokenDataReadSchema) -> list[CategoryWithCharacterCountSchema]:
        await self.valid_or_raise(token)
        return await self.service.get_all_by_character_id_with_character_count(token.character_id)