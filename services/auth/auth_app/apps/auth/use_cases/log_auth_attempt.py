import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..repositories.auth_logs import AuthLogRepositoryProtocol
from ..models import AuthLog


class LogAuthAttemptUseCaseProtocol(UseCaseProtocol[AuthLog], Protocol):
    async def __call__(
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


class LogAuthAttemptUseCase(LogAuthAttemptUseCaseProtocol):
    def __init__(self: Self, repository: AuthLogRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(
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
        return await self.repository.create(
            ip_address=ip_address,
            character_name=character_name,
            success=success,
            user_agent=user_agent,
            fingerprint=fingerprint,
            user_id=user_id,
            character_id=character_id,
            error_reason=error_reason,
        )