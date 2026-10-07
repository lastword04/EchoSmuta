from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.enums import UserRole
from ....core.use_cases import UseCaseProtocol
from ..schemas import (
    MailMessageRequestCreateSchema,
    MailMessageReadSchema
)
from ..services.mail_messages import MailMessageServiceProtocol
from ...messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class CreateMailMessageUseCaseProtocol(UseCaseProtocol[MailMessageReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, message: MailMessageRequestCreateSchema) -> MailMessageReadSchema:
        ...

class CreateMailMessageUseCase(CreateMailMessageUseCaseProtocol):
    def __init__(self: Self, service: MailMessageServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, token: UserTokenDataReadSchema, message: MailMessageRequestCreateSchema) -> MailMessageReadSchema:
        if token.role == UserRole.USER:
            await self.valid_or_raise(token)

        return await self.service.create(message, token.role, token.character_id)