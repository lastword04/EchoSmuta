from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol
from ...schemas import CategoryReadSchema
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class GetMyCategoriesUseCaseProtocol(UseCaseProtocol[list[CategoryReadSchema]]):
    async def __call__(self, token: UserTokenDataReadSchema) -> list[CategoryReadSchema]:
        ...

class GetMyCategoriesUseCase(GetMyCategoriesUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, token: UserTokenDataReadSchema) -> list[CategoryReadSchema]:
        await self.valid_or_raise(token)
        return await self.service.get_all_by_character_id(token.character_id)