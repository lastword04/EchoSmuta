import uuid
from typing import Protocol
from typing_extensions import Self
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ModeratorPermission


class ModeratorPermissionRepositoryProtocol(Protocol):
    session: AsyncSession

    async def get_by_user(self: Self, user_id: uuid.UUID) -> list[str]: ...
    async def add(
        self: Self, user_id: uuid.UUID, permission: str, granted_by: uuid.UUID
    ) -> ModeratorPermission: ...
    async def remove(self: Self, user_id: uuid.UUID, permission: str) -> bool: ...


class ModeratorPermissionRepository(ModeratorPermissionRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user(self: Self, user_id: uuid.UUID) -> list[str]:
        rows = await self.session.scalars(
            select(ModeratorPermission.permission).where(
                ModeratorPermission.user_id == user_id
            )
        )
        return list(rows)

    async def add(
        self: Self, user_id: uuid.UUID, permission: str, granted_by: uuid.UUID
    ) -> ModeratorPermission:
        existing = await self.session.scalar(
            select(ModeratorPermission).where(
                ModeratorPermission.user_id == user_id,
                ModeratorPermission.permission == permission,
            )
        )
        if existing is not None:
            return existing
        item = ModeratorPermission(
            user_id=user_id, permission=permission, granted_by=granted_by
        )
        self.session.add(item)
        await self.session.commit()
        return item

    async def remove(self: Self, user_id: uuid.UUID, permission: str) -> bool:
        result = await self.session.execute(
            delete(ModeratorPermission).where(
                ModeratorPermission.user_id == user_id,
                ModeratorPermission.permission == permission,
            )
        )
        await self.session.commit()
        return result.rowcount > 0
