from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...schemas import ExchangeSettingsReadSchema
from ...services.exchanges import ExchangeSettingsServiceProtocol 


class GetExchangeSettingsUseCaseProtocol(UseCaseProtocol[ExchangeSettingsReadSchema]):
    async def __call__(self: Self) -> ExchangeSettingsReadSchema:
        ...


class GetExchangeSettingsUseCase(GetExchangeSettingsUseCaseProtocol):
    def __init__(self: Self, service: ExchangeSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> ExchangeSettingsReadSchema:
        return (await self.service.get_all())[0]
