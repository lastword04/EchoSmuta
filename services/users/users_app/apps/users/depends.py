from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_async_session
from .repositories.users import UserRepository, UserRepositoryProtocol
from .repositories.users_info import (
    UserAdditionalInfoRepository,
    UserAdditionalInfoRepositoryProtocol,
)
from .repositories.moderator_permissions import (
    ModeratorPermissionRepository,
    ModeratorPermissionRepositoryProtocol,
)
from .services.users import UserService, UserServiceProtocol
from .services.passwords import PasswordService, PasswordServiceProtocol
from .use_cases.login import LoginUseCase, LoginUseCaseProtocol
from .use_cases.get import GetUserUseCase, GetUserUseCaseProtocol
from .use_cases.register import RegisterUserUseCase, RegisterUserUseCaseProtocol
from .use_cases.delete import DeleteUserUseCase, DeleteUserUseCaseProtocol
from .use_cases.get_by_email import GetByEmailUseCase, GetByEmailUseCaseProtocol
from .use_cases.change_password import (
    ChangePasswordUseCase,
    ChangePasswordUseCaseProtocol,
)
from .use_cases.moderator_permissions.get_permissions import (
    GetModeratorPermissionsUseCase,
    GetModeratorPermissionsUseCaseProtocol,
)


def __get_user_repository(
    session: AsyncSession = Depends(get_async_session),
) -> UserRepositoryProtocol:
    return UserRepository(session)


def get_user_additional_info_repository(
    session: AsyncSession = Depends(get_async_session),
) -> UserAdditionalInfoRepositoryProtocol:
    return UserAdditionalInfoRepository(session)


def get_password_service() -> PasswordServiceProtocol:
    return PasswordService()


def get_user_service(
    user_repository: UserRepositoryProtocol = Depends(__get_user_repository),
    password_service: PasswordServiceProtocol = Depends(get_password_service),
    user_additional_info_repository: UserAdditionalInfoRepositoryProtocol = Depends(
        get_user_additional_info_repository
    ),
) -> UserServiceProtocol:
    return UserService(
        user_repository, password_service, user_additional_info_repository
    )


def get_login_use_case(
    user_service: UserServiceProtocol = Depends(get_user_service),
) -> LoginUseCaseProtocol:
    return LoginUseCase(user_service)


def get_user_get_use_case(
    user_service: UserServiceProtocol = Depends(get_user_service),
) -> GetUserUseCaseProtocol:
    return GetUserUseCase(user_service)


def get_register_user_use_case(
    user_service: UserServiceProtocol = Depends(get_user_service),
) -> RegisterUserUseCaseProtocol:
    return RegisterUserUseCase(user_service)


def get_delete_user_use_case(
    user_service: UserServiceProtocol = Depends(get_user_service),
) -> DeleteUserUseCaseProtocol:
    return DeleteUserUseCase(user_service)


def get_user_by_email_use_case(
    user_service: UserServiceProtocol = Depends(get_user_service),
) -> GetByEmailUseCaseProtocol:
    return GetByEmailUseCase(user_service)


def get_change_password_use_case(
    user_service: UserServiceProtocol = Depends(get_user_service),
) -> ChangePasswordUseCaseProtocol:
    return ChangePasswordUseCase(user_service)


def get_moderator_permission_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ModeratorPermissionRepositoryProtocol:
    return ModeratorPermissionRepository(session)


def get_moderator_permissions_use_case(
    repository: ModeratorPermissionRepositoryProtocol = Depends(
        get_moderator_permission_repository
    ),
) -> GetModeratorPermissionsUseCaseProtocol:
    return GetModeratorPermissionsUseCase(repository)
