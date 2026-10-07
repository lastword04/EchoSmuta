from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from .....settings import settings
from ...schemas import ExchangeSettingsCreateSchema, ExchangeSettingsReadSchema
from ...services.exchanges import ExchangeSettingsServiceProtocol 


class InitializeExchangeSettingsUseCaseProtocol(UseCaseProtocol[ExchangeSettingsReadSchema]):
    async def __call__(self: Self) -> ExchangeSettingsReadSchema:
        ...


class InitializeExchangeSettingsUseCase(InitializeExchangeSettingsUseCaseProtocol):
    def __init__(self: Self, service: ExchangeSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> ExchangeSettingsReadSchema:

        exchange_settings = await self.service.get_all()

        if len(exchange_settings) > 0:
            return exchange_settings

        default_exchange_settings = self._get_default_exchange_settings()
        return await self.service.create(default_exchange_settings)

    def _get_default_exchange_settings(self: Self) -> ExchangeSettingsCreateSchema:
        return ExchangeSettingsCreateSchema(
            min_ducats_on_slot=settings.exchange_settings.min_ducats_on_slot,
            max_ducats_on_slot=settings.exchange_settings.max_ducats_on_slot,
            min_gold_on_slot=settings.exchange_settings.min_gold_on_slot,
            max_gold_on_slot=settings.exchange_settings.max_gold_on_slot,
            min_course_on_gold=settings.exchange_settings.min_course_on_gold,
            max_course_on_gold=settings.exchange_settings.max_course_on_gold,
            seller_on_ducats_tax=settings.exchange_settings.seller_on_ducats_tax
        )