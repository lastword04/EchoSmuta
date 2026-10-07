import logging
import hashlib
import secrets
from jose import jwt
from typing import Protocol, Optional
from typing_extensions import Self
from uuid import UUID
from datetime import datetime, timedelta, timezone
from shared.enums import UserRole
from shared.exceptions import InvalidTokenError 
from ....settings import settings
from ..schemas import (
    TokenReadSchema, RefreshTokenCreateDBSchema, RefreshTokenReadDBSchema,
    ResetTokenCreateSchema, ResetTokenReadSchema, ResetTokenSchema
)
from ..repositories.refresh_tokens import RefreshTokenRepositoryProtocol
from ..repositories.reset_tokens import ResetTokenRepositoryProtocol
from ..exceptions import TokenNotFoundError
from .passwords import PasswordServiceProtocol


logger = logging.getLogger(__name__)


class TokenServiceProtocol(Protocol):
    def create_access_token(self: Self, user_id: UUID, role: UserRole, 
                            is_main: bool, character_id: Optional[UUID] = None, 
                            expires_delta: Optional[timedelta] = None) -> TokenReadSchema:
        ...

    async def create_refresh_token(self: Self, user_id: UUID, is_main: bool, character_id: Optional[UUID] = None) -> TokenReadSchema:
        ...
    
    async def verify_refresh_token(self: Self, refresh_token: str) -> RefreshTokenReadDBSchema:
        ...
    
    async def delete(self: Self, id: UUID) -> bool:
        ...

    async def delete_all_by_character_id(self: Self, character_id: UUID) -> bool:
        ...

    async def delete_all_by_user_id(self: Self, user_id: UUID) -> bool:
        """
        Deletes all refresh tokens associated with a specific user ID.
        
        :param user_id: The UUID of the user whose refresh tokens should be deleted.
        :return: True if the tokens were deleted, False otherwise.
        """
        ...

    async def delete_refresh_token(self: Self, refresh_token: str) -> bool:
        """
        Deletes a refresh token by its hashed value.
        
        :param hashed_token: The hashed value of the refresh token to delete.
        :return: True if the token was deleted, False otherwise.
        """
        ...

class TokenService(TokenServiceProtocol):
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
        secret_key: str,
        algorithm: str,
        access_token_expire_minutes: int,
        refresh_token_expire_minutes: int
    ):
        self.refresh_token_repository = refresh_token_repository
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_minutes = refresh_token_expire_minutes

    async def delete(self: Self, id: UUID) -> bool:
        return await self.refresh_token_repository.delete(id)

    async def delete_all_by_character_id(self: Self, character_id: UUID) -> bool:
        return await self.refresh_token_repository.delete_all_by_character_id(character_id)

    async def delete_refresh_token(self: Self, refresh_token: str) -> bool:
        computed_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        return await self.refresh_token_repository.delete_by_hashed_token(computed_hash)

    async def delete_all_by_user_id(self: Self, user_id: UUID) -> bool:
        return await self.refresh_token_repository.delete_all_by_user_id(user_id)

    def create_access_token(
        self: Self, 
        user_id: UUID,
        role: UserRole, 
        is_main: bool,
        character_id: Optional[UUID] = None,
        expires_delta: Optional[timedelta] = None
    ) -> TokenReadSchema:
        logger.info(f"Creating access token for user: {user_id}")

        to_encode = {
            "user_id": str(user_id),
            "role": role,
            "is_main": is_main,
            **({"character_id": str(character_id)} if character_id is not None else {})
        }
        expiration = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=self.access_token_expire_minutes))
        to_encode.update({"exp": expiration})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Access token created for user: {user_id}")

        return TokenReadSchema(token=encoded_jwt,
                               expiration=expiration)

    async def create_refresh_token(self: Self, user_id: UUID, is_main: bool, character_id: Optional[UUID] = None) -> TokenReadSchema:
        logger.info(f"Creating refresh token for user: {user_id}")
        
        refresh_token = secrets.token_hex(32)

        expiration = datetime.now(timezone.utc) + timedelta(minutes=self.refresh_token_expire_minutes)
        
        hashed_refresh_token = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        token_count = await self.refresh_token_repository.count_by_user_id(user_id)
        logger.info(f"User {user_id} has {token_count} refresh tokens")

        if token_count >= 5:
            logger.info(f"User {user_id} has reached maximum refresh tokens, removing oldest")
            await self.refresh_token_repository.delete_oldest_by_user_id(user_id)
        
        await self.refresh_token_repository.create(RefreshTokenCreateDBSchema(
            user_id=user_id,
            character_id=character_id,
            hashed_refresh_token=hashed_refresh_token,
            is_main=is_main
        ))
        logger.info(f"Refresh token created for user: {user_id}")
        logger.debug(f"Refresh token: {refresh_token}, Expiration: {expiration}")
        return TokenReadSchema(
            token=refresh_token,
            expiration=expiration
        )


    async def verify_refresh_token(self: Self, refresh_token: str) -> RefreshTokenReadDBSchema:
        logger.info("Verifying refresh token")
        
        computed_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        
        db_refresh_token = await self.refresh_token_repository.get_by_hashed_token(computed_hash)
        
        if not db_refresh_token:
            logger.error("No matching refresh token found")
            raise InvalidTokenError()

        expiration = db_refresh_token.created_at + timedelta(minutes=self.refresh_token_expire_minutes)

        if datetime.now(timezone.utc) > expiration:
            logger.warning(f"Refresh token expired for user: {db_refresh_token.user_id}")
            await self.delete(db_refresh_token.id)
            raise InvalidTokenError()

        return db_refresh_token
    

class CleanupRefreshTokenServiceProtocol(Protocol):
    async def delete_all_expired_tokens(self: Self) -> bool:
        """
        Deletes all expired refresh tokens.
        
        :return: True if the tokens were deleted, False otherwise.
        """
        ...

class CleanupRefreshTokenService(CleanupRefreshTokenServiceProtocol):
    def __init__(self: Self, refresh_token_repository: RefreshTokenRepositoryProtocol):
        self.refresh_token_repository = refresh_token_repository

    async def delete_all_expired_tokens(self: Self) -> bool:
        return await self.refresh_token_repository.delete_all_expired_tokens()
    

class ResetTokenServiceProtocol(Protocol):
    async def generate_reset_token(self: Self, user_id: int) -> ResetTokenSchema:
        ...

    async def get_all(self: Self) -> list[ResetTokenReadSchema]:
        ...

    async def get_by_token(self: Self, token: str) -> ResetTokenReadSchema:
        ...

    async def delete(self: Self, id: UUID) -> bool:
        ...


class ResetTokenService(ResetTokenServiceProtocol):
    def __init__(self: Self, password_reset_repository: ResetTokenRepositoryProtocol,
                  password_service: PasswordServiceProtocol,
                  expire_minutes: int = settings.reset_token.expire_minutes):
        self.password_reset_repository = password_reset_repository
        self.password_service = password_service
        self.expire_minutes = expire_minutes

    async def generate_reset_token(self: Self, user_id: int) -> ResetTokenSchema:
        token = secrets.token_urlsafe(32)
        hashed_token = self.password_service.get_password_hash(token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        token_to_create = ResetTokenCreateSchema(
            user_id=user_id,
            token_hash=hashed_token,
            expires_at=expires_at
        )
        await self.password_reset_repository.create(token_to_create)
        reset_schema = ResetTokenSchema(
            token=token,
            minutes=self.expire_minutes
        )
        return reset_schema
    
    async def get_all(self: Self) -> list[ResetTokenReadSchema]:
        return await self.password_reset_repository.get_all()
    
    async def get_by_token(self: Self, token: str) -> ResetTokenReadSchema:
        db_tokens = await self.get_all()
        for db_token in db_tokens:
            if self.password_service.verify_password(token, db_token.token_hash):
                if db_token.created_at + timedelta(minutes=self.expire_minutes) < datetime.now(timezone.utc):
                    await self.password_reset_repository.delete(db_token.id)
                    raise TokenNotFoundError(value=token)
                return db_token
        raise TokenNotFoundError(value=token)

    async def delete(self: Self, id: UUID) -> bool:
        return await self.password_reset_repository.delete(id)
    
    
class CleanupResetPasswordServiceProtocol(Protocol):
    async def delete_all_expired_tokens(self: Self) -> bool:
        ...

class CleanupResetPasswordService(CleanupResetPasswordServiceProtocol):
    def __init__(self: Self, password_reset_repository: ResetTokenRepositoryProtocol):
        self.password_reset_repository = password_reset_repository

    async def delete_all_expired_tokens(self: Self) -> bool:
        return await self.password_reset_repository.delete_all_expired_tokens()