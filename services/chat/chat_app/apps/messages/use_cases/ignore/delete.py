import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ..chat.send_system_message import SendSystemMessageUseCaseProtocol
from ...services.ignore import IgnoreServiceProtocol
from ...enums import MessageType
from ..valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol


class DeleteIgnoreUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self, token: UserTokenDataReadSchema, ignore_character_id: uuid.UUID) -> bool:
        ...

class DeleteIgnoreUseCase(DeleteIgnoreUseCaseProtocol):
    def __init__(self, service: IgnoreServiceProtocol,
                 send_system_msg: SendSystemMessageUseCaseProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.service = service
        self.send_system_msg = send_system_msg
        self.valid_or_raise = valid_or_raise

    async def __call__(self, token: UserTokenDataReadSchema, ignore_character_id: uuid.UUID) -> bool:
        await self.valid_or_raise(token)
        is_delete = await self.service.delete(token.character_id, ignore_character_id)
        if is_delete:
            await self.send_system_msg(room="private",
                                       content="Я больше не игнорирую Ваши сообщения!",
                                        message_type=MessageType.IGNORE,
                                        is_trade=False,
                                        target_user_ids=[ignore_character_id],
                                        character_id=token.character_id)
        return is_delete