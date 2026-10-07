import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Protocol
from typing_extensions import Self
from ...models import Location, Character
from ...schemas import LocationCharacterCountSchema
 
class LocationsStatsRepositoryProtocol(Protocol):
    async def get_character_counts_by_location(self: Self) -> list[LocationCharacterCountSchema]:
        ...

class LocationsStatsRepository(LocationsStatsRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def get_character_counts_by_location(self: Self) -> list[LocationCharacterCountSchema]:
        async with self.session as session:
            stmt = (
                sa.select(
                    Location.slug.label('location_slug'),
                    Location.type.label('location_type'), # <-- Добавляем выбор поля type
                    sa.func.count(Character.id).label('character_count')
                )
                .select_from(Location)
                .outerjoin(
                    Character,
                    sa.and_(
                        Location.slug == Character.location_slug,
                        Character.is_online
                    )
                )
               .group_by(Location.id, Location.slug, Location.type) # <-- Добавляем Location.type
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                LocationCharacterCountSchema(
                    location_slug=row.location_slug,
                    count=row.character_count,
                    type=row.location_type # <-- Передаем новое поле в схему
                )
                for row in rows
            ]