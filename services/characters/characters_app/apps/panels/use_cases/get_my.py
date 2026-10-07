from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.panels import ItemsCRUServiceProtocol
from ..schemas import (
    CharacterFastItemReadSchema
)
from ...characters.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol 

class GetMyItemsUseCaseProtocol(UseCaseProtocol[CharacterFastItemReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterFastItemReadSchema:
        ...

class GetMyItemsUseCase(GetMyItemsUseCaseProtocol):
    def __init__(self: Self, items_service: ItemsCRUServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.items_service = items_service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterFastItemReadSchema:
        await self.valid_or_raise(token)
        return await self.items_service.get_for_character(token.character_id)