import uuid
from datetime import datetime

import sqlalchemy as sa
from typing_extensions import Self

from ....core.db import AsyncSession
from ..models import HouseGuestRequest


class HouseGuestRequestRepositoryProtocol:
    async def upsert_knock(self: Self, house_id: uuid.UUID, character_id: uuid.UUID, expires_at: datetime) -> HouseGuestRequest: ...
    async def get_by_id(self: Self, request_id: uuid.UUID) -> HouseGuestRequest | None: ...
    async def list_pending_by_house(self: Self, house_id: uuid.UUID, now: datetime) -> list[HouseGuestRequest]: ...
    async def delete_by_id(self: Self, request_id: uuid.UUID) -> bool: ...
    async def delete_by_character(self: Self, character_id: uuid.UUID) -> int: ...
    async def expire_old(self: Self, now: datetime) -> int: ...


class HouseGuestRequestRepository(HouseGuestRequestRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def upsert_knock(self: Self, house_id: uuid.UUID, character_id: uuid.UUID, expires_at: datetime) -> HouseGuestRequest:
        """Повторный стук в тот же дом не создаёт вторую заявку, а продлевает существующую."""
        async with self.session as session, session.begin():
            existing = (
                await session.execute(
                    sa.select(HouseGuestRequest)
                    .where(HouseGuestRequest.house_id == house_id)
                    .where(HouseGuestRequest.character_id == character_id)
                )
            ).scalar_one_or_none()
            if existing is not None:
                existing.expires_at = expires_at
                return existing
            request = HouseGuestRequest(
                house_id=house_id,
                character_id=character_id,
                expires_at=expires_at,
            )
            session.add(request)
            return request

    async def get_by_id(self: Self, request_id: uuid.UUID) -> HouseGuestRequest | None:
        async with self.session as session:
            return (
                await session.execute(
                    sa.select(HouseGuestRequest).where(HouseGuestRequest.id == request_id)
                )
            ).scalar_one_or_none()

    async def delete_by_character(self: Self, character_id: uuid.UUID) -> int:
        """Удаляет все заявки этого персонажа (во всех домах).

        Нужен при выходе гостя из дома: чтобы у владельца не висело
        «стучится…», даже если стук был сделан в другой дом или повторно.
        """
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(HouseGuestRequest).where(HouseGuestRequest.character_id == character_id)
            )
            return result.rowcount or 0

    async def list_pending_by_house(self: Self, house_id: uuid.UUID, now: datetime) -> list[HouseGuestRequest]:
        async with self.session as session:
            result = await session.execute(
                sa.select(HouseGuestRequest)
                .where(HouseGuestRequest.house_id == house_id)
                .where(HouseGuestRequest.expires_at > now)
                .order_by(HouseGuestRequest.created_at)
            )
            return list(result.scalars().all())

    async def delete_by_id(self: Self, request_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(HouseGuestRequest).where(HouseGuestRequest.id == request_id)
            )
            return (result.rowcount or 0) > 0

    async def expire_old(self: Self, now: datetime) -> int:
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(HouseGuestRequest).where(HouseGuestRequest.expires_at <= now)
            )
            return result.rowcount or 0