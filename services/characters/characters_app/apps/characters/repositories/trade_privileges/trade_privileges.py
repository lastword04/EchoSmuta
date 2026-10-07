import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import Character, CharacterTradePrivilege


class CharacterTradePrivilegeRepositoryProtocol(Protocol):
    async def get_gold_trade_enabled(self, character_id: uuid.UUID) -> bool: ...

    async def update_gold_trade_enabled(
        self,
        character_id: uuid.UUID,
        gold_trade_enabled: bool,
        updated_by_admin_id: uuid.UUID | None,
    ) -> CharacterTradePrivilege: ...


class CharacterTradePrivilegeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_gold_trade_enabled(self, character_id: uuid.UUID) -> bool:
        privilege = await self.session.scalar(
            select(CharacterTradePrivilege.gold_trade_enabled).where(
                CharacterTradePrivilege.character_id == character_id
            )
        )
        return privilege is True

    async def update_gold_trade_enabled(
        self,
        character_id: uuid.UUID,
        gold_trade_enabled: bool,
        updated_by_admin_id: uuid.UUID | None,
    ) -> CharacterTradePrivilege:
        character = await self.session.get(Character, character_id)
        if character is None:
            raise LookupError(character_id)

        privilege = await self.session.scalar(
            select(CharacterTradePrivilege)
            .where(CharacterTradePrivilege.character_id == character_id)
            .with_for_update()
        )
        if privilege is None:
            privilege = CharacterTradePrivilege(
                character_id=character_id,
                gold_trade_enabled=gold_trade_enabled,
                updated_by_admin_id=updated_by_admin_id,
            )
            self.session.add(privilege)
        else:
            privilege.gold_trade_enabled = gold_trade_enabled
            privilege.updated_by_admin_id = updated_by_admin_id

        await self.session.commit()
        await self.session.refresh(privilege)
        return privilege
