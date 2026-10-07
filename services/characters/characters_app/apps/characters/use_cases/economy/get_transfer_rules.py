from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.economy.transfer_value_settings import TransferValueCharactersSettingsServiceProtocol 
from ...schemas import TransferValueCharactersSettingsReadSchema

class GetTransferValueCharactersSettingsUseCaseProtocol(UseCaseProtocol[TransferValueCharactersSettingsReadSchema]):
    async def __call__(self: Self) -> TransferValueCharactersSettingsReadSchema:
        ...


class GetTransferValueCharactersSettingsUseCase(GetTransferValueCharactersSettingsUseCaseProtocol):
    def __init__(self: Self, service: TransferValueCharactersSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> TransferValueCharactersSettingsReadSchema:
        return (await self.service.get_all())[0]
