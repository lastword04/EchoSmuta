from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from ...repositories.sale.sale_history import SaleHistoryRepositoryProtocol
from ...schemas import SaleHistoryReadSchema


class GetSalesHistoryUseCaseProtocol(UseCaseProtocol[list[SaleHistoryReadSchema]], Protocol):
    async def __call__(self, user: UserTokenDataReadSchema, limit: int = 30) -> list[SaleHistoryReadSchema]: ...


class GetSalesHistoryUseCase:
    def __init__(self, repository: SaleHistoryRepositoryProtocol):
        self.repository = repository

    async def __call__(self, user: UserTokenDataReadSchema, limit: int = 30, location_slug: str | None = None) -> list[SaleHistoryReadSchema]:
        rows = await self.repository.list_by_seller(user.character_id, limit, location_slug)
        return [SaleHistoryReadSchema.model_validate(r) for r in rows]
    