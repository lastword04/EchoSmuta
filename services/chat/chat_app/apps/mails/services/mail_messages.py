import asyncio
import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.base import PaginationSchema, StatusOkSchema
from shared.enums import UserRole
from ....core.utils.exceptions import PermissionDeniedError
from ...categories.services.block_characters import CheckSendMailServiceProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..repositories.mail_messages import MailMessageRepositoryProtocol
from ..schemas import (
    MailMessageCreateSchema,
    MailMessageReadSchema,
    MailMessageRequestCreateSchema,
    MailMessagePaginationResultSchema
)
from ..enums import SenderStatus
from ..exceptions import CannotSendMessageToSelfError, CannotSendMessageToCharacterError
from .mail_recieve_settings import MailReceiveSettingsServiceProtocol
import logging
from ..events.mail_notifications import MailNotificationEventsProtocol

logger = logging.getLogger(__name__)


class MailMessageServiceProtocol(Protocol):
    async def create(
        self: Self,
        mail_message: MailMessageRequestCreateSchema,
        role: UserRole,
        from_character_id: Optional[uuid.UUID] = None
    ) -> MailMessageReadSchema:
        ...
    
    async def paginate_by_character_id(
        self: Self,
        pagination: PaginationSchema,
        character_id: uuid.UUID
    ) -> MailMessagePaginationResultSchema:
        ...

    async def paginate_my_by_character_id(
        self: Self,
        pagination: PaginationSchema,
        character_id: uuid.UUID
    ) -> MailMessagePaginationResultSchema:
        ...
    
    async def delete_for_sender(
        self: Self,
        message_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> StatusOkSchema:
        ...

    async def delete_for_recipient(
        self: Self,
        message_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> StatusOkSchema:
        ...


    async def update_all_messages_to_is_read(self: Self, character_id: uuid.UUID) -> bool:
        ...

    async def check_not_is_read_messages(self: Self, character_id: uuid.UUID) -> bool:
        ...

class MailMessageService(MailMessageServiceProtocol):
    def __init__(
        self: Self,
        repository: MailMessageRepositoryProtocol,
        character_service: CharacterServiceClientProtocol,
        mails_settings: MailReceiveSettingsServiceProtocol,
        category_mail_checker: CheckSendMailServiceProtocol,
        mail_events: MailNotificationEventsProtocol
    ):
        self.repository = repository
        self.character_service = character_service
        self.mails_settings = mails_settings
        self.category_mail_checker = category_mail_checker
        self.mail_events = mail_events


    async def create(
        self: Self,
        mail_message: MailMessageRequestCreateSchema,
        role: UserRole,
        from_character_id: Optional[uuid.UUID] = None
    ) -> MailMessageReadSchema:
        status = self._map_role_to_sender_status(role)

        from_character_result, to_character_result = None, None

        if from_character_id:
            # Любой персонаж (USER, ADMIN и т.д.) отправляет от своего имени
            results = await asyncio.gather(
                self.character_service.get_simple(from_character_id),
                self.character_service.get_by_name(mail_message.to_character_name),
                return_exceptions=True
            )
            from_character_result, to_character_result = results
        else:
            # Системные сообщения без отправителя
            from_character_result = None
            to_character_result = await self.character_service.get_by_name(mail_message.to_character_name)

        # Проверяем, была ли ошибка
        if isinstance(from_character_result, Exception):
            raise from_character_result  # или обрабатываем как-то по-другому

        if isinstance(to_character_result, Exception):
            raise to_character_result

        from_character = from_character_result
        to_character = to_character_result

        # Проверка что оба персонажа существуют
        if from_character_id and not from_character:
            raise ValueError("Sender character not found")

        if not to_character:
            raise ValueError("Recipient character not found")

        message_settings_recipient = await self.mails_settings.get_by_character_or_none(to_character.id)

        if to_character.id == from_character.id:
            raise CannotSendMessageToSelfError(from_character.id)

        if message_settings_recipient and message_settings_recipient.is_block_send_mails:
            raise CannotSendMessageToCharacterError(from_character.id, to_character.id)

        if not (await self.category_mail_checker.can_send_message(from_character.id, to_character.id)):
            raise CannotSendMessageToCharacterError(from_character.id, to_character.id)


        mail_message_create = MailMessageCreateSchema(
            from_character_name=from_character.name if from_character else None,
            from_character_id=from_character.id if from_character else None,
            to_character_name=to_character.name,
            to_character_id=to_character.id,
            message=mail_message.message,
            sender_status=status,
            is_read=False
        )

        created_mail = await self.repository.create(mail_message_create)

        # ✅ НОВОЕ: Отправляем уведомление о новом письме через WebSocket
        try:
            await self.mail_events.publish_mail_created(
                recipient_id=to_character.id,
                sender_name=from_character.name if from_character else "Система",
                message_preview=mail_message.message
            )
        except Exception as e:
            logger.error(f"Failed to publish mail notification: {e}")
            # Не бросаем исключение, письмо уже создано успешно

        return created_mail
    
    async def paginate_by_character_id(
        self: Self,
        pagination: PaginationSchema,
        character_id: uuid.UUID
    ) -> MailMessagePaginationResultSchema:
        return await self.repository.paginate_by_character_and_visibility(
            sorting=["-created_at"],
            pagination=pagination,
            user=None,
            policies=["messages:read"],
            to_character_id=character_id,
            )

    async def delete_for_sender(
        self: Self,
        message_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> StatusOkSchema:
        await self.repository.update_activity_sender_message(message_id, character_id)
        return StatusOkSchema()

    async def delete_for_recipient(
        self: Self,
        message_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> StatusOkSchema:
        await self.repository.update_activity_recipient_message(message_id, character_id)
        return StatusOkSchema()
        
    
    async def paginate_my_by_character_id(
        self: Self,
        pagination: PaginationSchema,
        character_id: uuid.UUID
    ) -> MailMessagePaginationResultSchema:
        return await self.repository.paginate_by_character_and_visibility(
            sorting=["-created_at"],
            pagination=pagination,
            user=None,
            policies=["messages:read"],
            from_character_id=character_id,
            )
    
    async def delete(
        self: Self,
        message_id: uuid.UUID,
        character_id: uuid.UUID
    ) -> bool:
        message = await self.repository.get(message_id)
        if message is None or message.to_character_id != character_id:
            raise PermissionDeniedError()
        return await self.repository.hide_message(message_id)
    
    async def update_all_messages_to_is_read(self: Self, character_id: uuid.UUID) -> bool:
        return await self.repository.update_all_messages_to_is_read(character_id)

    async def check_not_is_read_messages(self: Self, character_id: uuid.UUID) -> bool:
        return await self.repository.check_not_is_read_messages(character_id)

    def _map_role_to_sender_status(self, role: UserRole) -> SenderStatus:
        return SenderStatus.USER if role == UserRole.USER else SenderStatus.SYSTEM