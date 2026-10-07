from typing import Protocol

from ...repositories.economy.currency_operations import CharacterCurrencyOperationRepositoryProtocol
from ...schemas import CharacterCurrencyOperationFilters, CharacterCurrencyOperationListSchema


class CharacterCurrencyOperationServiceProtocol(Protocol):
    async def paginate(
        self,
        filters: CharacterCurrencyOperationFilters,
    ) -> CharacterCurrencyOperationListSchema: ...


class CharacterCurrencyOperationService:
    def __init__(self, repository: CharacterCurrencyOperationRepositoryProtocol) -> None:
        self.repository = repository

    async def paginate(
        self,
        filters: CharacterCurrencyOperationFilters,
    ) -> CharacterCurrencyOperationListSchema:
        return await self.repository.paginate(filters)
