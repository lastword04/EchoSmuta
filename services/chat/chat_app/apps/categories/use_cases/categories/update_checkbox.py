import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol
from ...schemas import CategoryWithCharacterCountSchema, CategoryUpdateCheckbox
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class UpdateCategoriesUseCaseProtocol(UseCaseProtocol[list[CategoryWithCharacterCountSchema]]):
    async def __call__(self, category_id: uuid.UUID, token: UserTokenDataReadSchema, update_data: CategoryUpdateCheckbox) -> list[CategoryWithCharacterCountSchema]:
        ...

class UpdateCategoriesUseCase(UpdateCategoriesUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, category_id: uuid.UUID, token: UserTokenDataReadSchema, update_data: CategoryUpdateCheckbox) -> list[CategoryWithCharacterCountSchema]:
        await self.valid_or_raise(token)
        return await self.service.update_checkbox_fields(category_id, token.character_id, update_data)