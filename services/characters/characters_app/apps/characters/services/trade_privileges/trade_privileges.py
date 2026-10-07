import uuid
from typing import Protocol

from ...repositories.trade_privileges.trade_privileges import CharacterTradePrivilegeRepositoryProtocol
from ...schemas import CharacterTradePrivilegeReadSchema


class CharacterTradePrivilegeServiceProtocol(Protocol):
    async def get_gold_trade_enabled(self, character_id: uuid.UUID) -> bool: ...

    async def update_gold_trade_enabled(
        self,
        character_id: uuid.UUID,
        gold_trade_enabled: bool,
        updated_by_admin_id: uuid.UUID | None,
    ) -> CharacterTradePrivilegeReadSchema: ...


class CharacterTradePrivilegeService:
    def __init__(self, repository: CharacterTradePrivilegeRepositoryProtocol) -> None:
        self.repository = repository

    async def get_gold_trade_enabled(self, character_id: uuid.UUID) -> bool:
        return await self.repository.get_gold_trade_enabled(character_id)

    async def update_gold_trade_enabled(
        self,
        character_id: uuid.UUID,
        gold_trade_enabled: bool,
        updated_by_admin_id: uuid.UUID | None,
    ) -> CharacterTradePrivilegeReadSchema:
        privilege = await self.repository.update_gold_trade_enabled(
            character_id,
            gold_trade_enabled,
            updated_by_admin_id,
        )
        return CharacterTradePrivilegeReadSchema.model_validate(privilege, from_attributes=True)
