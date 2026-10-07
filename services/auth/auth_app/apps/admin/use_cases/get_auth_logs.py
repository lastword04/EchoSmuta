from typing import Protocol
from typing_extensions import Self

from ....core.use_cases import UseCaseProtocol
from ...auth.repositories.auth_logs import AuthLogRepositoryProtocol
from ..schemas import AuthLogListSchema, AuthLogReadSchema, AuthLogFilters


class GetAuthLogsUseCaseProtocol(UseCaseProtocol[AuthLogListSchema], Protocol):
    async def __call__(self: Self, filters: AuthLogFilters) -> AuthLogListSchema: ...


class GetAuthLogsUseCase(GetAuthLogsUseCaseProtocol):
    def __init__(self: Self, repository: AuthLogRepositoryProtocol) -> None:
        self.repository = repository

    async def __call__(self: Self, filters: AuthLogFilters) -> AuthLogListSchema:
        logs, total = await self.repository.get_list(
            limit=filters.limit,
            offset=filters.offset,
            character_name=filters.character_name,
            user_id=filters.user_id,
            character_id=filters.character_id,
            success=filters.success,
            from_date=filters.from_date,
            to_date=filters.to_date,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )
        return AuthLogListSchema(
            objects=[AuthLogReadSchema.model_validate(log) for log in logs],
            count=total,
        )
