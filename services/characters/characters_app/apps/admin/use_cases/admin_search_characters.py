from typing import Protocol
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..repositories.admin_characters import AdminCharacterRepositoryProtocol
from ..schemas import AdminCharacterListSchema, AdminCharacterReadSchema, AdminCharacterSearchFilters


class AdminSearchCharactersUseCaseProtocol(UseCaseProtocol[AdminCharacterListSchema], Protocol):
    async def __call__(self: Self, filters: AdminCharacterSearchFilters) -> AdminCharacterListSchema: ...


class AdminSearchCharactersUseCase(AdminSearchCharactersUseCaseProtocol):
    def __init__(self: Self, repository: AdminCharacterRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self: Self, filters: AdminCharacterSearchFilters) -> AdminCharacterListSchema:
        characters, total = await self.repository.search(
            limit=filters.limit,
            offset=filters.offset,
            name=filters.name,
            name_like=filters.name_like,
            character_id=filters.character_id,
            user_id=filters.user_id,
            is_active=filters.is_active,
            is_online=filters.is_online,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )
        return AdminCharacterListSchema(
            objects=[AdminCharacterReadSchema.model_validate(c) for c in characters],
            count=total,
        )
