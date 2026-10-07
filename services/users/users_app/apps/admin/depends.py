from fastapi import Depends

from shared.permissions import ensure_admin
from shared.schemas.auth import UserTokenDataReadSchema

from ...core.depends import get_user_token_payload
from ..users.depends import get_moderator_permission_repository
from ..users.repositories.moderator_permissions import (
    ModeratorPermissionRepositoryProtocol,
)
from .use_cases.grant_permission import (
    GrantModeratorPermissionUseCase,
    GrantModeratorPermissionUseCaseProtocol,
)
from .use_cases.revoke_permission import (
    RevokeModeratorPermissionUseCase,
    RevokeModeratorPermissionUseCaseProtocol,
)


def require_admin(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
) -> UserTokenDataReadSchema:
    ensure_admin(token)
    return token


def get_grant_moderator_permission_use_case(
    repository: ModeratorPermissionRepositoryProtocol = Depends(
        get_moderator_permission_repository
    ),
) -> GrantModeratorPermissionUseCaseProtocol:
    return GrantModeratorPermissionUseCase(repository)


def get_revoke_moderator_permission_use_case(
    repository: ModeratorPermissionRepositoryProtocol = Depends(
        get_moderator_permission_repository
    ),
) -> RevokeModeratorPermissionUseCaseProtocol:
    return RevokeModeratorPermissionUseCase(repository)
