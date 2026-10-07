import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from sqlalchemy import select, func, asc, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ...characters.models import Character


class AdminCharacterRepositoryProtocol(Protocol):
    async def search(
        self: Self,
        limit: int = 50,
        offset: int = 0,
        name: Optional[str] = None,
        name_like: Optional[str] = None, 
        character_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        is_online: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Character], int]: ...

    async def get_by_id(self: Self, character_id: uuid.UUID) -> Optional[Character]: ...

    async def set_banned(self: Self, character_id: uuid.UUID, is_active: bool) -> Optional[Character]: ...

    async def get_all_by_user(self: Self, user_id: uuid.UUID) -> list[Character]: ...

    async def set_banned_by_user(self: Self, user_id: uuid.UUID, is_banned: bool) -> list[Character]: ...


class AdminCharacterRepository(AdminCharacterRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self: Self,
        limit: int = 50,
        offset: int = 0,
        name: Optional[str] = None,
        name_like: Optional[str] = None, 
        character_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        is_online: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Character], int]:
        query = select(Character)
        count_query = select(func.count()).select_from(Character)

        if name is not None:
            query = query.where(func.lower(Character.name) == name.lower())
            count_query = count_query.where(func.lower(Character.name) == name.lower())
        if name_like is not None:
            query = query.where(Character.name.ilike(f"%{name_like}%"))
            count_query = count_query.where(Character.name.ilike(f"%{name_like}%"))
        if character_id is not None:
            query = query.where(Character.id == character_id)
            count_query = count_query.where(Character.id == character_id)
        if user_id is not None:
            query = query.where(Character.user_id == user_id)
            count_query = count_query.where(Character.user_id == user_id)
        if is_active is not None:
            query = query.where(Character.is_active == is_active)
            count_query = count_query.where(Character.is_active == is_active)
        if is_online is not None:
            query = query.where(Character.is_online == is_online)
            count_query = count_query.where(Character.is_online == is_online)

        sort_column = getattr(Character, sort_by, Character.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        query = query.offset(offset).limit(limit)

        rows = await self.session.scalars(query)
        total = await self.session.scalar(count_query)

        return list(rows), total or 0

    async def get_by_id(self: Self, character_id: uuid.UUID) -> Optional[Character]:
        return await self.session.get(Character, character_id)

    async def set_banned(self: Self, character_id: uuid.UUID, is_banned: bool) -> Optional[Character]:
        character = await self.session.get(Character, character_id)
        if character is None:
            return None
        character.is_banned = is_banned
        await self.session.commit()
        return character

    async def get_all_by_user(self: Self, user_id: uuid.UUID) -> list[Character]:
        query = (
            select(Character)
            .where(Character.user_id == user_id)
            .order_by(desc(Character.created_at))
        )
        rows = await self.session.scalars(query)
        return list(rows)

    async def set_banned_by_user(self: Self, user_id: uuid.UUID, is_banned: bool) -> list[Character]:
        characters = await self.get_all_by_user(user_id)
        for character in characters:
            character.is_banned = is_banned
        await self.session.commit()
        return characters
