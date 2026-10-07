from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.mail_recieve_settings import MailReceiveSettingsServiceProtocol
from ...schemas import MailRecieveSettingsReadSchema
from ....messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class CreateMailsSettingsUseCaseProtocol(UseCaseProtocol[MailRecieveSettingsReadSchema]):
    async def __call__(self, token: UserTokenDataReadSchema) -> MailRecieveSettingsReadSchema:
        ...

class CreateMailsSettingsUseCase(CreateMailsSettingsUseCaseProtocol):
    def __init__(self, service: MailReceiveSettingsServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, token: UserTokenDataReadSchema) -> MailRecieveSettingsReadSchema:
        await self.valid_or_raise(token)

        return await self.service.create_default(token.character_id)