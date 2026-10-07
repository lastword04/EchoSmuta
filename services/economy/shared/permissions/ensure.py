from fastapi import HTTPException
from ..enums import UserRole
from ..schemas.auth import UserTokenDataReadSchema
from .client import UsersInternalClientProtocol


def ensure_admin(token: UserTokenDataReadSchema) -> None:
    """Проверяет что пользователь  ADMIN. Иначе 403."""
    if token.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='Admin role is required')


async def ensure_permission(
    token: UserTokenDataReadSchema,
    permission: str,
    client: UsersInternalClientProtocol
) -> None:
    """
    Проверяет право модератора.
    
    - ADMIN: всегда разрешено
    - MODERATOR: проверяет наличие права через users internal
    - USER: 403
    
    Raises:
        HTTPException(403) если нет права
    """
    if token.role == UserRole.ADMIN:
        return
    
    if token.role != UserRole.MODERATOR:
        raise HTTPException(status_code=403, detail='Insufficient permissions')
    
    permissions = await client.get_user_permissions(token.user_id)
    
    if permission not in permissions:
        raise HTTPException(status_code=403, detail=f'Missing permission: {permission}')
