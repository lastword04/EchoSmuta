from fastapi import Depends

from shared.permissions import ensure_admin
from shared.schemas.auth import UserTokenDataReadSchema

from ...core.depends import get_user_token_payload
from ..auth.depends import get_auth_log_repository
from ..auth.repositories.auth_logs import AuthLogRepositoryProtocol
from .use_cases.get_auth_logs import GetAuthLogsUseCase, GetAuthLogsUseCaseProtocol


def require_admin(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
) -> UserTokenDataReadSchema:
    ensure_admin(token)
    return token


def get_auth_logs_use_case(
    repository: AuthLogRepositoryProtocol = Depends(get_auth_log_repository),
) -> GetAuthLogsUseCaseProtocol:
    return GetAuthLogsUseCase(repository=repository)
