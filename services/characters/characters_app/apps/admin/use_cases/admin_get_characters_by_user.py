import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.admin_characters import AdminCharacterRepositoryProtocol
from ..schemas import AdminCharacterReadSchema


class AdminGetCharactersByUserUseCaseProtocol(Protocol):
    async def __call__(self: Self, user_id: uuid.UUID) -> list[AdminCharacterReadSchema]: ...


class AdminGetCharactersByUserUseCase(AdminGetCharactersByUserUseCaseProtocol):
    def __init__(self: Self, repository: AdminCharacterRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self: Self, user_id: uuid.UUID) -> list[AdminCharacterReadSchema]:
        characters = await self.repository.get_all_by_user(user_id)
        return [AdminCharacterReadSchema.model_validate(c) for c in characters]
