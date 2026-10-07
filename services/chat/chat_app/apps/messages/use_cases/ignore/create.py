from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ..chat.send_system_message import SendSystemMessageUseCaseProtocol
from ...services.ignore import IgnoreServiceProtocol
from ...schemas import IgnoreRequestSchema, IgnoreReadSchema
from ...enums import MessageType
from ..valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol


class CreateIgnoreUseCaseProtocol(UseCaseProtocol[IgnoreReadSchema]):
    async def __call__(self, token: UserTokenDataReadSchema, data: IgnoreRequestSchema) -> IgnoreReadSchema:
        ...

class CreateIgnoreUseCase(CreateIgnoreUseCaseProtocol):
    def __init__(self, service: IgnoreServiceProtocol,
                 send_system_msg: SendSystemMessageUseCaseProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.send_system_msg = send_system_msg
        self.valid_or_raise = valid_or_raise

    async def __call__(self, token: UserTokenDataReadSchema, data: IgnoreRequestSchema) -> IgnoreReadSchema:
        await self.valid_or_raise(token)
        ignore = await self.service.create(token.character_id, data)
        await self.send_system_msg(room="private",
                                   content="Я игнорирую Ваши сообщения!",
                                    message_type=MessageType.IGNORE,
                                    is_trade=False,
                                    target_user_ids=[ignore.ignored_character_id],
                                    character_id=ignore.character_id)
        return ignore