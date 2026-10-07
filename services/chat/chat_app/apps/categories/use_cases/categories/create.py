from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol
from ...schemas import CategoryWithCharacterCountSchema, CategoryCreateSchema
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class CreateCategoriesUseCaseProtocol(UseCaseProtocol[list[CategoryWithCharacterCountSchema]]):
    async def __call__(self, category: CategoryCreateSchema, token: UserTokenDataReadSchema) -> list[CategoryWithCharacterCountSchema]:
        ...

class CreateCategoriesUseCase(CreateCategoriesUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, category: CategoryCreateSchema, token: UserTokenDataReadSchema) -> list[CategoryWithCharacterCountSchema]:
        await self.valid_or_raise(token)
        return await self.service.create(category, token.character_id)