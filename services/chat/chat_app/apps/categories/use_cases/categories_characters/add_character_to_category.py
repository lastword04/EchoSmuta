import uuid
from typing import Optional
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.categories_characters import CategoryCharacterServiceProtocol
from ...schemas import CategoryWithCharactersReadSchema
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class AddCharacterToCategoryUseCaseProtocol(UseCaseProtocol[CategoryWithCharactersReadSchema]):
    async def __call__(self, category_id: uuid.UUID, character_name: str, token: UserTokenDataReadSchema, is_online: Optional[bool]) -> CategoryWithCharactersReadSchema:
        ...

class AddCharacterToCategoryUseCase(AddCharacterToCategoryUseCaseProtocol):
    def __init__(self, service: CategoryCharacterServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, category_id: uuid.UUID, character_name: str, token: UserTokenDataReadSchema, is_online: Optional[bool]) -> CategoryWithCharactersReadSchema:
        await self.valid_or_raise(token)
        return await self.service.add_by_character_name_to_category(category_id, character_name, token.character_id, is_online)
    