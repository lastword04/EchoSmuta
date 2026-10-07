import uuid
from universal_profanity.profanity import UniversalProfanity
import redis.asyncio as redis
from typing import Protocol, Optional
from shared.schemas.characters import CharacterListIds
from ..repositories.messages import MessageRepositoryProtocol
from ..adapter.characters import CharacterServiceClientProtocol
from ..enums import MessageType
from ..schemas import MessageCreateSchema, MessageRequestSchema, MessageReadSchema
from ..exceptions import ChatDisabledError
from .publisher import RedisPublisherProtocol
from .filters import FilterProtocol
from .settings import ChatSettingsServiceProtocol

class MessageServiceProtocol(Protocol):
    async def create_message(self, character_id: uuid.UUID, room: str, message: MessageRequestSchema) -> MessageReadSchema:
        ...

    async def create_message_direct(self, message_type: Optional[MessageType], room: str, message: MessageRequestSchema, character_id: Optional[uuid.UUID] = None) -> MessageReadSchema:
        ...

class MessageService(MessageServiceProtocol):
    def __init__(
        self,
        repository: MessageRepositoryProtocol,
        chat_settings_serivce: ChatSettingsServiceProtocol,
        character_service: CharacterServiceClientProtocol,
        profanities: list[UniversalProfanity],
        filters: list[FilterProtocol] 
    ):
        self.repository = repository
        self.chat_settings_serivce = chat_settings_serivce
        self.character_service = character_service
        self.profanities = profanities
        self.filters = filters

    async def create_message(
        self,
        character_id: uuid.UUID,
        room: str,
        message: MessageRequestSchema,
    ) -> MessageReadSchema:
        settings = await self.chat_settings_serivce.get_by_character_id(character_id)
        if not settings.chat_enabled:
            raise ChatDisabledError(character_id)
        return await self._create_message(None, character_id, room, message)

    async def create_message_direct(
        self,
        message_type: Optional[MessageType],
        room: str,
        message: MessageRequestSchema,
        character_id: Optional[uuid.UUID] = None,
    ) -> MessageReadSchema:
        return await self._create_message(message_type, character_id, room, message)

    async def _create_message(
        self,
        message_type: Optional[MessageType],
        character_id: Optional[uuid.UUID],
        room: str,
        message: MessageRequestSchema,
    ) -> MessageReadSchema:
        censored_text = message.content
        is_trade = not message.is_private and message.is_trade
        if room != "system":
            for profanity in self.profanities:
                censored_text = profanity.censor(censored_text)

            for filter in self.filters:
                censored_text = filter.filter_text(censored_text)
        sender = await self.character_service.get_simple(character_id) if character_id else None
        target_names_characters = None
        result_user_ids = message.target_user_ids
        if result_user_ids:
            characters_ids = CharacterListIds(ids=message.target_user_ids)
            target_characters = await self.character_service.get_list_simple_characters_by_ids(characters_ids)
            target_names_characters = [character.name for character in target_characters.characters]
            result_user_ids = [character.id for character in target_characters.characters]
        message_create = MessageCreateSchema(
            sender_id=character_id,
            sender_name=sender.name if sender else None,
            message_type=message_type,
            room=room,
            content=censored_text,
            original_content=message.content,
            target_user_ids=result_user_ids,
            target_user_names=target_names_characters,
            is_trade=is_trade,
        )
        return await self.repository.create(message_create)
    
class SendAndPublishMessageService(MessageServiceProtocol):
    def __init__(self, message_service: MessageServiceProtocol, publisher: RedisPublisherProtocol):
        self.message_service = message_service
        self.publisher = publisher
    
    async def create_message(self, character_id: uuid.UUID, room: str, message: MessageRequestSchema) -> MessageReadSchema:
        result_message = await self.message_service.create_message(
            room=room,
            message=message,
            character_id=character_id,
        )

        await self.publisher.publish_to_room(
            room=room,
            message=result_message.model_dump(mode="json")
        )

        return result_message

    async def create_message_direct(
        self,
        message_type: Optional[MessageType],
        room: str,
        message: MessageRequestSchema,
        character_id: Optional[uuid.UUID] = None,
    ) -> MessageReadSchema:
        result_message = await self.message_service.create_message_direct(
            message_type=message_type,
            room=room,
            message=message,
            character_id=character_id
        )

        await self.publisher.publish_to_room(
            room=room,
            message=result_message.model_dump(mode="json")
        )

        return result_message
    

    