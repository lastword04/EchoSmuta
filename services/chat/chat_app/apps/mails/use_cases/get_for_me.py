from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ..schemas import (
    MailMessagePaginationResultSchema
)
from ..services.mail_messages import MailMessageServiceProtocol
from ...messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class GetMailMessageForMeUseCaseProtocol(UseCaseProtocol[MailMessagePaginationResultSchema]):
    async def __call__(self: Self, limit: int, offset: int, token: UserTokenDataReadSchema) -> MailMessagePaginationResultSchema:
        ...

class GetMailMessageForMeUseCase(GetMailMessageForMeUseCaseProtocol):
    def __init__(self: Self, service: MailMessageServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.valid_or_raise = valid_or_raise

    async def __call__(self: Self, limit: int, offset: int, token: UserTokenDataReadSchema) -> MailMessagePaginationResultSchema:
        await self.valid_or_raise(token)
        pagination = PaginationSchema(limit=limit, offset=offset)
        results = await self.service.paginate_by_character_id(pagination, token.character_id)
        await self.service.update_all_messages_to_is_read(token.character_id)
        return results