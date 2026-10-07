import uuid
from datetime import datetime
from typing import Protocol
from typing_extensions import Self
import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl, BaseRepositoryProtocol
from ..models import CharacterBuff
from ..schemas import CharacterBuffReadSchema


class BuffRepositoryProtocol(Protocol):
    async def get_by_character_and_type(self: Self, character_id: uuid.UUID, buff_type: str) -> CharacterBuff | None: ...
    async def get_active_by_character(self: Self, character_id: uuid.UUID) -> list[CharacterBuff]: ...
    async def delete_by_character_and_type(self: Self, character_id: uuid.UUID, buff_type: str) -> None: ...
    async def deactivate_duplicates(self: Self, character_id: uuid.UUID, buff_type: str, exclude_id: uuid.UUID | None = None) -> None: ...
    async def create_buff(self: Self, buff: CharacterBuff) -> CharacterBuff: ...
    async def update_buff(self: Self, buff: CharacterBuff) -> CharacterBuff: ...


class BuffRepository(BaseRepositoryImpl[CharacterBuff, CharacterBuffReadSchema, None, None], BuffRepositoryProtocol):
    
    async def get_by_character_and_type(self, character_id: uuid.UUID, buff_type: str) -> CharacterBuff | None:
        async with self.session as s:
            stmt = sa.select(CharacterBuff).where(
                CharacterBuff.character_id == character_id,
                CharacterBuff.buff_type == buff_type,
                CharacterBuff.is_active == True
            )
            result = await s.execute(stmt)
            return result.scalar_one_or_none()

    async def get_active_by_character(self, character_id: uuid.UUID) -> list[CharacterBuff]:
        async with self.session as s:
            stmt = sa.select(CharacterBuff).where(
                CharacterBuff.character_id == character_id,
                CharacterBuff.is_active == True
            )
            result = await s.execute(stmt)
            return list(result.scalars().all())

    async def delete_by_character_and_type(self, character_id: uuid.UUID, buff_type: str) -> None:
        async with self.session as s:
            stmt = sa.update(CharacterBuff).where(
                CharacterBuff.character_id == character_id,
                CharacterBuff.buff_type == buff_type
            ).values(is_active=False)
            await s.execute(stmt)
            await s.commit()   

    async def deactivate_duplicates(self, character_id: uuid.UUID, buff_type: str, exclude_id: uuid.UUID | None = None) -> None:
        """Деактивировать все дубликаты buff'а данного типа"""
        async with self.session as s:
            stmt = sa.update(CharacterBuff).where(
                CharacterBuff.character_id == character_id,
                CharacterBuff.buff_type == buff_type,
            )
            if exclude_id:
                stmt = stmt.where(CharacterBuff.id != exclude_id)
            stmt = stmt.values(is_active=False)
            await s.execute(stmt)
            await s.commit()
    
    async def create_buff(self, buff: CharacterBuff) -> CharacterBuff:
        """Создать бафф напрямую из SQLAlchemy модели"""
        async with self.session as s:
            s.add(buff)
            await s.commit()
            await s.refresh(buff)
            return buff

    async def update_buff(self, buff: CharacterBuff) -> CharacterBuff:
        """Обновить бафф напрямую из SQLAlchemy модели"""
        async with self.session as s:
            s.add(buff)
            await s.commit()
            await s.refresh(buff)
            return buff