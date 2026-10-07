import uuid
import sqlalchemy as sa
from typing import Protocol
from typing_extensions import Self
from shared.schemas.characters import CharacterItemsBalance
from ...models import Character
from .....core.db import AsyncSession
from .....core.utils.exceptions import ModelNotFoundException


class CharacterItemsBalanceRepositoryProtocol(Protocol):
    async def get_character_item_balance(self: Self, character_id: uuid.UUID) -> CharacterItemsBalance:
        ...

class CharacterItemsBalanceRepository(CharacterItemsBalanceRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def get_character_item_balance(self: Self, character_id: uuid.UUID) -> CharacterItemsBalance:
        async with self.session as session:
            stmt = self._get_need_fields().where(Character.id == character_id)

            model = (await session.execute(stmt)).mappings().one_or_none()

            if model is None:
                raise ModelNotFoundException(Character, character_id)
            
            return CharacterItemsBalance.model_validate(model, from_attributes=True)


    def _get_need_fields(self: Self) -> sa.Select:
        return (
            sa.select(Character.id, Character.name, Character.level,
                      Character.is_online, Character.location_slug, Character.ducats)
        )
