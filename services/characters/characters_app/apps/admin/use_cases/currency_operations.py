from ....core.use_cases import UseCaseProtocol
from ...characters.schemas import CharacterCurrencyOperationFilters, CharacterCurrencyOperationListSchema
from ...characters.services.economy.currency_operations import CharacterCurrencyOperationServiceProtocol


class GetCharacterCurrencyOperationsUseCaseProtocol(UseCaseProtocol[CharacterCurrencyOperationListSchema]):
    async def __call__(
        self,
        filters: CharacterCurrencyOperationFilters,
    ) -> CharacterCurrencyOperationListSchema: ...


class GetCharacterCurrencyOperationsUseCase(GetCharacterCurrencyOperationsUseCaseProtocol):
    def __init__(self, service: CharacterCurrencyOperationServiceProtocol) -> None:
        self.service = service

    async def __call__(
        self,
        filters: CharacterCurrencyOperationFilters,
    ) -> CharacterCurrencyOperationListSchema:
        return await self.service.paginate(filters)
