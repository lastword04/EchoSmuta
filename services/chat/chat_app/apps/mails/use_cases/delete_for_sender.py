import uuid
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.mail_messages import MailMessageServiceProtocol
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema
from ...messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class DeleteForSenderMailMessageUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, message_id: uuid.UUID, token: UserTokenDataReadSchema) -> StatusOkSchema:
        ...

class DeleteForSenderMailMessageUseCase(DeleteForSenderMailMessageUseCaseProtocol):
    def __init__(self: Self, service: MailMessageServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, message_id: uuid.UUID, token: UserTokenDataReadSchema) -> StatusOkSchema:
        await self.valid_or_raise(token)
        return await self.service.delete_for_sender(message_id, token.character_id)