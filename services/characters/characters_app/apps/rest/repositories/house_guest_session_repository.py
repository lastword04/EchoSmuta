import uuid

import sqlalchemy as sa
from typing_extensions import Self

from ....core.db import AsyncSession
from ..models import HouseGuestSession


class HouseGuestSessionRepositoryProtocol:
    async def create(self: Self, house_id: uuid.UUID, character_id: uuid.UUID) -> HouseGuestSession: ...
    async def get_by_character(self: Self, character_id: uuid.UUID) -> HouseGuestSession | None: ...
    async def list_by_house(self: Self, house_id: uuid.UUID) -> list[HouseGuestSession]: ...
    async def count_by_house(self: Self, house_id: uuid.UUID) -> int: ...
    async def delete_by_character(self: Self, character_id: uuid.UUID) -> bool: ...


class HouseGuestSessionRepository(HouseGuestSessionRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def create(self: Self, house_id: uuid.UUID, character_id: uuid.UUID) -> HouseGuestSession:
        async with self.session as session, session.begin():
            session_obj = HouseGuestSession(house_id=house_id, character_id=character_id)
            session.add(session_obj)
            return session_obj

    async def get_by_character(self: Self, character_id: uuid.UUID) -> HouseGuestSession | None:
        async with self.session as session:
            return (
                await session.execute(
                    sa.select(HouseGuestSession).where(HouseGuestSession.character_id == character_id)
                )
            ).scalar_one_or_none()

    async def list_by_house(self: Self, house_id: uuid.UUID) -> list[HouseGuestSession]:
        async with self.session as session:
            result = await session.execute(
                sa.select(HouseGuestSession)
                .where(HouseGuestSession.house_id == house_id)
                .order_by(HouseGuestSession.created_at)
            )
            return list(result.scalars().all())

    async def count_by_house(self: Self, house_id: uuid.UUID) -> int:
        async with self.session as session:
            result = await session.execute(
                sa.select(sa.func.count())
                .select_from(HouseGuestSession)
                .where(HouseGuestSession.house_id == house_id)
            )
            return int(result.scalar_one())

    async def delete_by_character(self: Self, character_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(HouseGuestSession).where(HouseGuestSession.character_id == character_id)
            )
            return (result.rowcount or 0) > 0