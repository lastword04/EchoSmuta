import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from typing_extensions import Self
from shared.schemas.characters import CharacterListIds
from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import CharacterActivity, Character
from ...schemas import (
    CharacterActivityCreateDBSchema, CharacterActivityUpdateDBSchema, 
    CharacterActivityReadSchema
)


class CharacterActivityRepositoryProtocol(
    BaseRepositoryImpl[
        CharacterActivity,
        CharacterActivityReadSchema,
        CharacterActivityCreateDBSchema,
        CharacterActivityUpdateDBSchema
    ]
):
    async def get_inactive_characters_id(self: Self) -> CharacterListIds:
        ...

    async def delete_all_old_activity(self: Self) -> bool:
        ...

class CharacterActivityRepository(CharacterActivityRepositoryProtocol):
    def __init__(self, session: AsyncSession, inactive_minutes: int, delete_after_minutes: int):
        self.inactive_minutes = inactive_minutes
        self.delete_after_minutes = delete_after_minutes
        super().__init__(session)
        
    async def get_inactive_characters_id(self: Self) -> CharacterListIds:
        async with self.session as session:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.inactive_minutes)
            
            # Подзапрос для нахождения последней активности
            last_activity_subq = (
                sa.select(
                    self.model_type.character_id,
                    sa.func.max(self.model_type.created_at).label('last_activity')
                )
                .group_by(self.model_type.character_id)
                .subquery()
            )
            
            # Основной запрос с фильтром по is_online
            stmt = (
                sa.select(Character.id)
                .join(
                    last_activity_subq, 
                    Character.id == last_activity_subq.c.character_id
                )
                .where(
                    sa.and_(
                        last_activity_subq.c.last_activity < cutoff_time,
                        Character.is_online
                    )
                )
            )
            
            result = await session.execute(stmt)
            inactive_characters_ids = result.scalars().all()
            return CharacterListIds(ids=inactive_characters_ids)
        

    async def delete_all_old_activity(self: Self) -> bool:
        async with self.session as session, session.begin():
            expired_time = datetime.now(timezone.utc) - timedelta(minutes=self.delete_after_minutes)
            stmt = (
                sa.delete(self.model_type).where(self.model_type.created_at < expired_time)
            )

            await session.execute(stmt)

            return True
