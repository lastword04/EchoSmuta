import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.characters import CharacterItemsBalance
from ...repositories.mining.items import CharacterItemsBalanceRepositoryProtocol


class CharacterItemsBalanceServiceProtocol(Protocol):
    async def get_character_item_balance(self: Self, character_id: uuid.UUID) -> CharacterItemsBalance:
        ...

class CharacterItemsBalanceService(CharacterItemsBalanceServiceProtocol):
    def __init__(self: Self, repository: CharacterItemsBalanceRepositoryProtocol):
        self.repository = repository

    async def get_character_item_balance(self: Self, character_id: uuid.UUID) -> CharacterItemsBalance:
        return await self.repository.get_character_item_balance(character_id)

