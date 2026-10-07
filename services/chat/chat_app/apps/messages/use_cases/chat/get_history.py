from typing import Optional
from fastapi import HTTPException

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import PaginationSchema
from shared.exceptions import CharacterIsNotOnlineError
from .....core.use_cases import UseCaseProtocol
from ...services.chat_history import ChatHistoryServiceProtocol
from ...adapter.characters import CharacterServiceClientProtocol
from ...schemas import MessagePaginationReadSchema
from .valid_room import ValidRoomUseCaseProtocol


class GetChatHistoryUseCaseProtocol(UseCaseProtocol[MessagePaginationReadSchema]):
    async def __call__(self, room: str, location_slug: Optional[str], token: UserTokenDataReadSchema, limit: int, offset: int) -> MessagePaginationReadSchema:
        ...


class GetChatHistoryUseCase(GetChatHistoryUseCaseProtocol):
    def __init__(
        self,
        room_validator: ValidRoomUseCaseProtocol,
        chat_history: ChatHistoryServiceProtocol,
        characters_service: CharacterServiceClientProtocol,
    ):
        self.room_validator = room_validator
        self.chat_history = chat_history
        self.characters_service = characters_service

    async def __call__(self, room: str, location_slug: Optional[str], token: UserTokenDataReadSchema, limit: int, offset: int) -> MessagePaginationReadSchema:
        is_valid = await self.room_validator(room, token)
        if not is_valid:
            raise CharacterIsNotOnlineError()

        # Изоляция виртуальных комнат (дом, номер гостиницы).
        # Обычные локации (1.19.residential-area, 1.12.inn) — публичные:
        # любой, кто стоит на улице, читает их историю. А house:uuid и
        # inn:inside — не публичные: доступ только у тех, кто сейчас внутри.
        # Проверка через существующий фильтр /online?room_id=... — если
        # персонаж в комнате, он вернётся в списке.
        if room.startswith("house:") or room == "inn:inside":
            online = await self.characters_service.get_online_characters(
                limit=100, offset=0, room_id=room
            )
            member_ids = {u.id for u in online.objects}
            if token.character_id not in member_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Нет доступа к чату этой комнаты",
                )

        paginate_schema = PaginationSchema(
            limit=limit,
            offset=offset
        )
        return await self.chat_history.get_chat_history(token.character_id, room, location_slug, paginate_schema)