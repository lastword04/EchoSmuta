import uuid
from typing import Protocol
from typing_extensions import Self

from ....core.use_cases import UseCaseProtocol
from ...users.repositories.moderator_permissions import (
    ModeratorPermissionRepositoryProtocol,
)


class GrantModeratorPermissionUseCaseProtocol(UseCaseProtocol[bool], Protocol):
    async def __call__(
        self: Self, user_id: uuid.UUID, permission: str, granted_by: uuid.UUID
    ) -> bool: ...


class GrantModeratorPermissionUseCase(GrantModeratorPermissionUseCaseProtocol):
    def __init__(self: Self, repository: ModeratorPermissionRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(
        self: Self, user_id: uuid.UUID, permission: str, granted_by: uuid.UUID
    ) -> bool:
        await self.repository.add(user_id, permission, granted_by)
        return True
