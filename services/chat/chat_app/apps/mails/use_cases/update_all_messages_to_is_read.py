from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.mail_messages import MailMessageServiceProtocol
from ...messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class UpdateMailMessagesToIsReadUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> bool:
        ...

class UpdateMailMessagesToIsReadUseCase(UpdateMailMessagesToIsReadUseCaseProtocol):
    def __init__(self: Self, service: MailMessageServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> bool:
        await self.valid_or_raise(token)

        return await self.service.update_all_messages_to_is_read(token.character_id)