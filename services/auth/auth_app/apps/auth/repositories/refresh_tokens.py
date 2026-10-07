import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing_extensions import Self
from datetime import datetime, timedelta, timezone
from ....settings import settings
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import RefreshToken
from ..schemas import RefreshTokenReadDBSchema, RefreshTokenUpdateDBSchema, RefreshTokenCreateDBSchema


class RefreshTokenRepositoryProtocol(BaseRepositoryImpl[
    RefreshToken,
    RefreshTokenReadDBSchema,
    RefreshTokenCreateDBSchema,
    RefreshTokenUpdateDBSchema
]):
    async def count_by_character_id(self: Self, character_id: UUID) -> int:
        ...

    async def get_oldest_by_character_id(self: Self, character_id: UUID) -> RefreshTokenReadDBSchema:
        ...

    async def count_by_user_id(self: Self, user_id: UUID) -> int:
        ...

    async def get_oldest_by_user_id(self: Self, user_id: UUID) -> RefreshTokenReadDBSchema:
        ...

    async def delete_oldest_by_user_id(self: Self, user_id: UUID) -> bool:
        ...
    
    async def get_by_hashed_token(self: Self, hashed_token: str) -> RefreshTokenReadDBSchema:
        ...

    async def delete_all_by_character_id(self: Self, character_id: UUID) -> bool:
        ...

    async def delete_by_hashed_token(self: Self, hashed_token: str) -> bool:
        ...

    async def delete_all_by_user_id(self: Self, user_id: UUID) -> bool:
        ...

    async def delete_all_expired_tokens(self: Self) -> bool:
        """
        Deletes all expired refresh tokens.
        
        :return: True if the tokens were deleted, False otherwise.
        """
        ...

class RefreshTokenRepository(RefreshTokenRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession, expire_minutes: int = settings.refresh_token.expire_minutes):
        self.expire_minutes = expire_minutes
        super().__init__(session=session)

    async def count_by_character_id(self: Self, character_id: UUID) -> int:
        async with self.session as session:
            stmt = sa.select(sa.func.count(self.model_type.id)).where(
                self.model_type.character_id == character_id
            )
            result = await session.execute(stmt)
            count = result.scalar()
            return count

    async def get_oldest_by_character_id(self: Self, character_id: UUID) -> RefreshTokenReadDBSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id)
                .order_by(self.model_type.created_at.asc())
                .limit(1)
            )
            token = (await session.execute(stmt)).scalar_one_or_none()
            if token is None:
                return None
            return self.read_schema_type.model_validate(token, from_attributes=True)

    async def count_by_user_id(self: Self, user_id: UUID) -> int:
        async with self.session as session:
            stmt = sa.select(sa.func.count(self.model_type.id)).where(
                self.model_type.user_id == user_id
            )
            result = await session.execute(stmt)
            count = result.scalar()
            return count

    async def delete_oldest_by_user_id(self: Self, user_id: UUID) -> bool:
        async with self.session as session, session.begin():
            subquery = (
                sa.select(sa.func.min(self.model_type.created_at).label('oldest_date'))
                .where(self.model_type.user_id == user_id)
                .scalar_subquery()
            )
            
            stmt = (
                sa.delete(self.model_type)
                .where(
                    self.model_type.user_id == user_id,
                    self.model_type.created_at == subquery
                )
            )
            
            await session.execute(stmt)
            
            return True

    async def get_by_hashed_token(self: Self, hashed_token: str) -> RefreshTokenReadDBSchema:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(
                self.model_type.hashed_refresh_token == hashed_token
            )
            token = (await session.execute(stmt)).scalar_one_or_none()
            if token is None:
               return None
            return self.read_schema_type.model_validate(token, from_attributes=True)
        
    async def delete_by_hashed_token(self: Self, hashed_token: str) -> bool:
        async with self.session as session, session.begin():
            stmt = sa.delete(self.model_type).where(
                self.model_type.hashed_refresh_token == hashed_token
            )
            result = await session.execute(stmt)
            return result.rowcount > 0
    
    async def delete_all_by_character_id(self: Self, character_id: UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = sa.delete(self.model_type).where(
                self.model_type.character_id == character_id
            )
            await session.execute(stmt)
            
            return True
        
    async def delete_all_by_user_id(self: Self, user_id: UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = sa.delete(self.model_type).where(
                self.model_type.user_id == user_id
            )
            result = await session.execute(stmt)
            return result.rowcount > 0
        
    async def delete_all_expired_tokens(self: Self) -> bool:
        async with self.session as session, session.begin():
            expiration_time = datetime.now(timezone.utc) - timedelta(minutes=self.expire_minutes)
            stmt = sa.delete(self.model_type).where(
                self.model_type.created_at < expiration_time
            )
            await session.execute(stmt)
            return True