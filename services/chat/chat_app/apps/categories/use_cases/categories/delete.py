import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class DeleteCategoriesUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, category_id: uuid.UUID, token: UserTokenDataReadSchema) -> bool:
        ...

class DeleteCategoriesUseCase(DeleteCategoriesUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, category_id: uuid.UUID, token: UserTokenDataReadSchema) -> bool:
        await self.valid_or_raise(token)
        return await self.service.delete(category_id, token.character_id)