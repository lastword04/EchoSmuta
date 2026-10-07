from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.mail_recieve_settings import MailReceiveSettingsServiceProtocol
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class DeleteMailsSettingsUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, token: UserTokenDataReadSchema) -> bool:
        ...

class DeleteMailsSettingsUseCase(DeleteMailsSettingsUseCaseProtocol):
    def __init__(self, service: MailReceiveSettingsServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, token: UserTokenDataReadSchema) -> bool:
        await self.valid_or_raise(token)

        return await self.service.delete_by_character_id(token.character_id)