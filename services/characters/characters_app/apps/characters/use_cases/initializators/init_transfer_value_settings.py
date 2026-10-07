from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from .....settings import settings
from ...schemas import TransferValueCharactersSettingsReadSchema, TransferValueCharactersSettingsCreateSchema
from ...services.economy.transfer_value_settings import TransferValueCharactersSettingsServiceProtocol 


class InitializeTransferValueSettingsUseCaseProtocol(UseCaseProtocol[TransferValueCharactersSettingsReadSchema]):
    async def __call__(self: Self) -> TransferValueCharactersSettingsReadSchema:
        ...


class InitializeTransferValueSettingsUseCase(InitializeTransferValueSettingsUseCaseProtocol):
    def __init__(self: Self, service: TransferValueCharactersSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> TransferValueCharactersSettingsReadSchema:

        transfer_settings = await self.service.get_all()

        if len(transfer_settings) > 0:
            return transfer_settings

        default_transfer_settings = self._get_default_transfer_settings()
        return await self.service.create(default_transfer_settings)

    def _get_default_transfer_settings(self: Self) -> TransferValueCharactersSettingsCreateSchema:
        return TransferValueCharactersSettingsCreateSchema(
            min_transfer_level=settings.transfer_value_characters_settings.min_transfer_level,
            min_transfer_ducats=settings.transfer_value_characters_settings.min_transfer_ducats,
            min_transfer_gold=settings.transfer_value_characters_settings.min_transfer_gold,
            transfer_tax_percentage=settings.transfer_value_characters_settings.transfer_tax_percentage
        )