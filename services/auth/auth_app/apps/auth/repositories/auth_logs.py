import uuid
from datetime import datetime
from typing import Protocol, Optional
from typing_extensions import Self
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import AuthLog


class AuthLogRepositoryProtocol(Protocol):
    async def create(
        self: Self,
        ip_address: str,
        character_name: str,
        success: bool,
        user_agent: Optional[str] = None,
        fingerprint: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        character_id: Optional[uuid.UUID] = None,
        error_reason: Optional[str] = None,
    ) -> AuthLog: ...
    
    async def get_list(
        self: Self,
        limit: int = 50,
        offset: int = 0,
        character_name: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        character_id: Optional[uuid.UUID] = None,
        success: Optional[bool] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AuthLog], int]: ...


class AuthLogRepository(AuthLogRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self: Self,
        ip_address: str,
        character_name: str,
        success: bool,
        user_agent: Optional[str] = None,
        fingerprint: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        character_id: Optional[uuid.UUID] = None,
        error_reason: Optional[str] = None,
    ) -> AuthLog:
        log = AuthLog(
            ip_address=ip_address,
            user_agent=user_agent,
            fingerprint=fingerprint,
            character_name=character_name,
            user_id=user_id,
            character_id=character_id,
            success=success,
            error_reason=error_reason,
        )
        self.session.add(log)
        await self.session.commit()
        return log

    async def get_list(
        self: Self,
        limit: int = 50,
        offset: int = 0,
        character_name: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        character_id: Optional[uuid.UUID] = None,
        success: Optional[bool] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AuthLog], int]:
        query = select(AuthLog)
        count_query = select(func.count()).select_from(AuthLog)

        if character_name is not None:
            query = query.where(AuthLog.character_name == character_name)
            count_query = count_query.where(AuthLog.character_name == character_name)
        if user_id is not None:
            query = query.where(AuthLog.user_id == user_id)
            count_query = count_query.where(AuthLog.user_id == user_id)
        if character_id is not None:
            query = query.where(AuthLog.character_id == character_id)
            count_query = count_query.where(AuthLog.character_id == character_id)
        if success is not None:
            query = query.where(AuthLog.success == success)
            count_query = count_query.where(AuthLog.success == success)
        if from_date is not None:
            query = query.where(AuthLog.created_at >= from_date)
            count_query = count_query.where(AuthLog.created_at >= from_date)
        if to_date is not None:
            query = query.where(AuthLog.created_at <= to_date)
            count_query = count_query.where(AuthLog.created_at <= to_date)

        sort_column = getattr(AuthLog, sort_by, AuthLog.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        query = query.offset(offset).limit(limit)

        rows = await self.session.scalars(query)
        total = await self.session.scalar(count_query)

        return list(rows), total or 0