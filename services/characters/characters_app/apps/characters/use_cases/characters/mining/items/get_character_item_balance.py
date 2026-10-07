import uuid
from typing_extensions import Self
from .......core.use_cases import UseCaseProtocol
from .....services.mining.items import CharacterItemsBalanceServiceProtocol
from shared.schemas.characters import CharacterItemsBalance

class GetCharacterItemBalanceUseCaseProtocol(UseCaseProtocol[CharacterItemsBalance]):
     async def __call__(self: Self, character_id: uuid.UUID,) -> CharacterItemsBalance:
        ...

class GetCharacterItemBalanceUseCase(GetCharacterItemBalanceUseCaseProtocol):
    def __init__(self: Self, service: CharacterItemsBalanceServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID,) -> CharacterItemsBalance:
        return await self.service.get_character_item_balance(character_id)