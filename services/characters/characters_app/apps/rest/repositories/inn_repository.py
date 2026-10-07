import uuid
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import RestRental, RestRentalHistory


class RestRepositoryProtocol:
    async def create_rental(self, character_id: uuid.UUID, room_number: int, days: int,
                            rented_at: datetime, expires_at: datetime) -> RestRental: ...
    async def get_active_rental(self, character_id: uuid.UUID) -> Optional[RestRental]: ...
    async def get_first_free_room_number(self, max_rooms: int) -> int: ...
    async def count_active_rentals(self) -> int: ...
    async def expire_rental(self, rental_id: uuid.UUID) -> bool: ...
    async def get_expired_rental_for_character(self, character_id: uuid.UUID, now: datetime) -> Optional[RestRental]: ...
    async def get_expired_rentals(self, now: datetime) -> list[RestRental]: ...
    async def create_history(self, character_id: uuid.UUID, days: int,
                             rented_at: datetime, expired_at: datetime) -> RestRentalHistory: ...


class RestRepository(RestRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_rental(self, character_id: uuid.UUID, room_number: int, days: int,
                            rented_at: datetime, expires_at: datetime) -> RestRental:
        async with self.session as session, session.begin():
            rental = RestRental(
                character_id=character_id,
                room_number=room_number,
                days=days,
                rented_at=rented_at,
                expires_at=expires_at
            )
            session.add(rental)
        return rental

    async def get_active_rental(self, character_id: uuid.UUID) -> Optional[RestRental]:
        async with self.session as session:
            stmt = (
                sa.select(RestRental)
                .where(
                    RestRental.character_id == character_id,
                    RestRental.expires_at > datetime.now(timezone.utc)
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_first_free_room_number(self, max_rooms: int) -> int:
        async with self.session as session:
            stmt = sa.text(f"""
                SELECT MIN(rn) FROM generate_series(1, :max_rooms) AS t(rn)
                WHERE rn NOT IN (
                    SELECT room_number FROM rest_rentals
                    WHERE expires_at > NOW()
                )
            """)
            result = await session.execute(stmt, {"max_rooms": max_rooms})
            room = result.scalar_one()
            return room if room else 1

    async def count_active_rentals(self) -> int:
        async with self.session as session:
            stmt = sa.select(sa.func.count()).select_from(RestRental).where(
                RestRental.expires_at > datetime.now(timezone.utc)
            )
            result = await session.execute(stmt)
            return result.scalar_one()

    async def expire_rental(self, rental_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = sa.delete(RestRental).where(RestRental.id == rental_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    async def get_expired_rental_for_character(self, character_id: uuid.UUID, now: datetime) -> Optional[RestRental]:
        async with self.session as session:
            stmt = (
                sa.select(RestRental)
                .where(
                    RestRental.character_id == character_id,
                    RestRental.expires_at <= now,
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_expired_rentals(self, now: datetime) -> list[RestRental]:
        async with self.session as session:
            stmt = sa.select(RestRental).where(RestRental.expires_at <= now)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_history(self, character_id: uuid.UUID, days: int,
                             rented_at: datetime, expired_at: datetime) -> RestRentalHistory:
        async with self.session as session, session.begin():
            history = RestRentalHistory(
                character_id=character_id,
                days=days,
                rented_at=rented_at,
                expired_at=expired_at
            )
            session.add(history)
        return history