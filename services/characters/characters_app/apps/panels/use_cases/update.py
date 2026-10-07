import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol 
from ..services.panels import ItemsCRUServiceProtocol
from ..schemas import (
    CharacterFastItemUpdateSchema,
    CharacterFastItemReadSchema
)

class UpdateItemsUseCaseProtocol(UseCaseProtocol[CharacterFastItemReadSchema]):
    async def __call__(self: Self, items_id: uuid.UUID, data: CharacterFastItemUpdateSchema, character: UserTokenDataReadSchema) -> CharacterFastItemReadSchema:
        ...

class UpdateItemsUseCase(UpdateItemsUseCaseProtocol):
    def __init__(self: Self, items_service: ItemsCRUServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.items_service = items_service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, items_id: uuid.UUID, data: CharacterFastItemUpdateSchema, character: UserTokenDataReadSchema) -> CharacterFastItemReadSchema:
        await self.valid_or_raise(character)
        return await self.items_service.update(items_id, data, character.character_id)