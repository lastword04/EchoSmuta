import uuid
from typing import Protocol
from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol
from ...repositories.moderator_permissions import ModeratorPermissionRepositoryProtocol


class GetModeratorPermissionsUseCaseProtocol(UseCaseProtocol[list[str]], Protocol):
    async def __call__(self: Self, user_id: uuid.UUID) -> list[str]: ...


class GetModeratorPermissionsUseCase(GetModeratorPermissionsUseCaseProtocol):
    def __init__(self: Self, repository: ModeratorPermissionRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self: Self, user_id: uuid.UUID) -> list[str]:
        return await self.repository.get_by_user(user_id)
