import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema

from ..users.depends import get_moderator_permissions_use_case
from ..users.schemas import PermissionListResponse
from ..users.use_cases.moderator_permissions.get_permissions import (
    GetModeratorPermissionsUseCaseProtocol,
)
from .depends import (
    get_grant_moderator_permission_use_case,
    get_revoke_moderator_permission_use_case,
    require_admin,
)
from .schemas import PermissionRequest
from .use_cases.grant_permission import GrantModeratorPermissionUseCaseProtocol
from .use_cases.revoke_permission import RevokeModeratorPermissionUseCaseProtocol

router = APIRouter(
    prefix="/api/users",
    tags=["Users Admin"],
    dependencies=[Depends(require_admin)],
)


# Admin endpoints для управления правами
@router.get("/admin/users/{user_id}/permissions", response_model=PermissionListResponse)
async def get_user_permissions_admin(
    user_id: uuid.UUID = Path(...),
    use_case: GetModeratorPermissionsUseCaseProtocol = Depends(
        get_moderator_permissions_use_case
    ),
) -> PermissionListResponse:
    permissions = await use_case(user_id)
    return PermissionListResponse(user_id=user_id, permissions=permissions)


@router.post("/admin/users/{user_id}/permissions", response_model=bool)
async def grant_user_permission(
    data: PermissionRequest,
    user_id: uuid.UUID = Path(...),
    admin: UserTokenDataReadSchema = Depends(require_admin),
    use_case: GrantModeratorPermissionUseCaseProtocol = Depends(
        get_grant_moderator_permission_use_case
    ),
) -> bool:
    return await use_case(user_id, data.permission, admin.user_id)


@router.delete("/admin/users/{user_id}/permissions", response_model=bool)
async def revoke_user_permission(
    data: PermissionRequest,
    user_id: uuid.UUID = Path(...),
    use_case: RevokeModeratorPermissionUseCaseProtocol = Depends(
        get_revoke_moderator_permission_use_case
    ),
) -> bool:
    return await use_case(user_id, data.permission)
