from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.economy.character_transfer import CharacterTransferServiceProtocol 
from ...schemas import CharacterTransferRequestSchema, TransferResult


class TransferValueCharacterUseCaseProtocol(UseCaseProtocol[TransferResult]):
    async def __call__(self: Self, character: CharacterTransferRequestSchema, token: UserTokenDataReadSchema) -> TransferResult:
        ...


class TransferValueCharacterUseCase(TransferValueCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterTransferServiceProtocol):
        self.service = service

    async def __call__(self: Self, character: CharacterTransferRequestSchema, token: UserTokenDataReadSchema) -> TransferResult:
        return await self.service.transfer_character(character, token.user_id)
