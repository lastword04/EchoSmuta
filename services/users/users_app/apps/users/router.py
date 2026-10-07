from fastapi import APIRouter, Depends, Path
import uuid
from shared.schemas.users import (
    UserReadSchema,
    UserCreateSchema,
    UserLoginSchema,
    PasswordSchema,
)
from ...core.depends import get_service_token_payload
from .use_cases.login import LoginUseCaseProtocol
from .use_cases.get import GetUserUseCaseProtocol
from .use_cases.register import RegisterUserUseCaseProtocol
from .use_cases.delete import DeleteUserUseCaseProtocol
from .use_cases.get_by_email import GetByEmailUseCaseProtocol
from .use_cases.change_password import ChangePasswordUseCaseProtocol
from .use_cases.moderator_permissions.get_permissions import (
    GetModeratorPermissionsUseCaseProtocol,
)
from .schemas import PermissionListResponse
from .depends import (
    get_login_use_case,
    get_user_get_use_case,
    get_register_user_use_case,
    get_delete_user_use_case,
    get_user_by_email_use_case,
    get_change_password_use_case,
    get_moderator_permissions_use_case,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/login", response_model=UserReadSchema)
async def login(
    user_data: UserLoginSchema,
    token_payload: dict = Depends(get_service_token_payload),
    login_use_case: LoginUseCaseProtocol = Depends(get_login_use_case),
) -> UserReadSchema:
    user = await login_use_case(user_data)
    return user


@router.post("/register", response_model=UserReadSchema, status_code=201)
async def register(
    user: UserCreateSchema,
    token_payload: dict = Depends(get_service_token_payload),
    register_use_case: RegisterUserUseCaseProtocol = Depends(
        get_register_user_use_case
    ),
) -> UserReadSchema:
    return await register_use_case(user)


@router.get("/{user_id}", response_model=UserReadSchema)
async def get_user(
    user_id: str = Path(
        ..., title="User ID", description="The ID of the user to retrieve"
    ),
    token_payload: dict = Depends(get_service_token_payload),
    get_user_use_case: GetUserUseCaseProtocol = Depends(get_user_get_use_case),
) -> UserReadSchema:
    return await get_user_use_case(user_id)


@router.put("/{user_id}/change-password", response_model=UserReadSchema)
async def change_password(
    password: PasswordSchema,
    user_id: str = Path(
        ..., title="User ID", description="The ID of the user to change password"
    ),
    token_payload: dict = Depends(get_service_token_payload),
    change_password_use_case: ChangePasswordUseCaseProtocol = Depends(
        get_change_password_use_case
    ),
) -> UserReadSchema:
    return await change_password_use_case(user_id, password)


@router.get("/email/{email}", response_model=UserReadSchema)
async def get_user_by_email(
    email: str = Path(
        ..., title="User Email", description="The email of the user to retrieve"
    ),
    token_payload: dict = Depends(get_service_token_payload),
    get_user_by_email_use_case: GetByEmailUseCaseProtocol = Depends(
        get_user_by_email_use_case
    ),
) -> UserReadSchema:
    return await get_user_by_email_use_case(email)


@router.delete("/{user_id}", response_model=None, status_code=204)
async def delete_user(
    user_id: str = Path(
        ..., title="User ID", description="The ID of the user to delete"
    ),
    token_payload: dict = Depends(get_service_token_payload),
    delete_user_use_case: DeleteUserUseCaseProtocol = Depends(get_delete_user_use_case),
) -> None:
    await delete_user_use_case(user_id)
    return None


# Internal endpoint для проверки прав из других сервисов
@router.get(
    "/internal/users/{user_id}/permissions", response_model=PermissionListResponse
)
async def get_user_permissions_internal(
    user_id: uuid.UUID = Path(...),
    token_payload: dict = Depends(get_service_token_payload),
    use_case: GetModeratorPermissionsUseCaseProtocol = Depends(
        get_moderator_permissions_use_case
    ),
) -> PermissionListResponse:
    permissions = await use_case(user_id)
    return PermissionListResponse(user_id=user_id, permissions=permissions)
