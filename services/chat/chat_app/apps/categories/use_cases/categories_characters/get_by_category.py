import uuid
from typing import Optional
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories_characters import CategoryCharacterServiceProtocol
from ...schemas import CategoryWithCharactersReadSchema
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class GetByCategoryUseCaseProtocol(UseCaseProtocol[CategoryWithCharactersReadSchema]):
    async def __call__(self, category_id: uuid.UUID, token: UserTokenDataReadSchema, is_onlie: Optional[bool]) -> CategoryWithCharactersReadSchema:
        ...

class GetByCategoryUseCase(GetByCategoryUseCaseProtocol):
    def __init__(self, service: CategoryCharacterServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, category_id: uuid.UUID, token: UserTokenDataReadSchema, is_onlie: Optional[bool]) -> CategoryWithCharactersReadSchema:
        await self.valid_or_raise(token)
        return await self.service.get_by_category_id(category_id, token.character_id, is_onlie)
    