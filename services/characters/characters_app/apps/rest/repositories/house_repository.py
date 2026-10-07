import uuid
import sqlalchemy as sa
from typing_extensions import Self
from ..models import House


class HouseRepositoryProtocol:
    async def next_number(self: Self) -> int: ...
    async def create(self: Self, owner_id: uuid.UUID, number: int, location_slug: str, capacity: int) -> House: ...
    async def get_by_id(self: Self, house_id: uuid.UUID) -> House | None: ...
    async def list_by_owner(self: Self, owner_id: uuid.UUID) -> list[House]: ...
    async def set_current_volume(self: Self, house_id: uuid.UUID, volume: int) -> None: ...
    async def set_regen_multipliers(self: Self, house_id: uuid.UUID, multipliers: dict) -> None: ...
    async def set_wallpaper_photo_id(self: Self, house_id: uuid.UUID, photo_id: uuid.UUID | None) -> None: ...
    async def get_by_number(self: Self, number: int) -> House | None: ...

class HouseRepository(HouseRepositoryProtocol):
    def __init__(self: Self, session):
        self.session = session

    async def next_number(self: Self) -> int:
        async with self.session as session:
            result = await session.execute(sa.text("SELECT nextval('house_number_seq')"))
            return result.scalar_one()

    async def create(self: Self, owner_id, number, location_slug, capacity) -> House:
        async with self.session as session, session.begin():
            house = House(
                owner_character_id=owner_id,
                number=number,
                location_slug=location_slug,
                capacity=capacity,
            )
            session.add(house)
        return house

    async def get_by_id(self: Self, house_id) -> House | None:
        async with self.session as session:
            return await session.get(House, house_id)

    async def list_by_owner(self: Self, owner_id) -> list[House]:
        async with self.session as session:
            stmt = (
                sa.select(House)
                .where(House.owner_character_id == owner_id)
                .order_by(House.number.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def set_current_volume(self: Self, house_id: uuid.UUID, volume: int) -> None:
        async with self.session as session, session.begin():
            await session.execute(
                sa.update(House)
                .where(House.id == house_id)
                .values(current_volume=volume)
            )

    async def set_regen_multipliers(self: Self, house_id: uuid.UUID, multipliers: dict) -> None:
        async with self.session as session, session.begin():
            await session.execute(
                sa.update(House)
                .where(House.id == house_id)
                .values(regen_multipliers=multipliers)
            )

    async def set_wallpaper_photo_id(self: Self, house_id: uuid.UUID, photo_id: uuid.UUID | None) -> None:
        async with self.session as session, session.begin():
            await session.execute(
                sa.update(House)
                .where(House.id == house_id)
                .values(wallpaper_photo_id=photo_id)
            )

    async def get_by_number(self: Self, number: int) -> House | None:
        async with self.session as session:
            return (
                await session.execute(
                    sa.select(House).where(House.number == number)
                )
            ).scalar_one_or_none()