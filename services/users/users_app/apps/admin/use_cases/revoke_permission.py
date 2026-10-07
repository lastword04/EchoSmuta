import uuid
from typing import Protocol
from typing_extensions import Self

from ....core.use_cases import UseCaseProtocol
from ...users.repositories.moderator_permissions import (
    ModeratorPermissionRepositoryProtocol,
)


class RevokeModeratorPermissionUseCaseProtocol(UseCaseProtocol[bool], Protocol):
    async def __call__(self: Self, user_id: uuid.UUID, permission: str) -> bool: ...


class RevokeModeratorPermissionUseCase(RevokeModeratorPermissionUseCaseProtocol):
    def __init__(self: Self, repository: ModeratorPermissionRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self: Self, user_id: uuid.UUID, permission: str) -> bool:
        return await self.repository.remove(user_id, permission)
