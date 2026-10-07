import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Self
from datetime import datetime, timedelta, timezone
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....settings import settings
from ..models import PasswordResetTokens
from ..schemas import ResetTokenCreateSchema, ResetTokenUpdateSchema, ResetTokenReadSchema


class ResetTokenRepositoryProtocol(BaseRepositoryImpl[
    PasswordResetTokens,
    ResetTokenReadSchema,
    ResetTokenCreateSchema,
    ResetTokenUpdateSchema
]):
    async def delete_all_expired_tokens(self: Self) -> bool:
        ...

class ResetTokenRepository(ResetTokenRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession, expire_minutes: int = settings.reset_token.expire_minutes):
        self.expire_minutes = expire_minutes
        super().__init__(session=session)
    async def delete_all_expired_tokens(self: Self) -> bool:
        async with self.session as session, session.begin():
            expiration_time = datetime.now(timezone.utc) - timedelta(minutes=self.expire_minutes)
            stmt = sa.delete(self.model_type).where(
                self.model_type.created_at < expiration_time
                )
            await session.execute(stmt)

            return True
        