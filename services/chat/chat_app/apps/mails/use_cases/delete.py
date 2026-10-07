import uuid
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.mail_messages import MailMessageServiceProtocol
from shared.schemas.auth import UserTokenDataReadSchema
from ...messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class DeleteMailMessageUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self, message_id: uuid.UUID, token: UserTokenDataReadSchema) -> bool:
        ...

class DeleteMailMessageUseCase(DeleteMailMessageUseCaseProtocol):
    def __init__(self: Self, service: MailMessageServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, message_id: uuid.UUID, token: UserTokenDataReadSchema) -> bool:
        await self.valid_or_raise(token)
        return await self.service.delete(message_id, token.character_id)