import redis.asyncio as redis
from fastapi import Depends
from universal_profanity.profanity import UniversalProfanity
from typing import Callable
from shared.services.tokens_utils import DecodeAccessTokenProtocol
from shared.services.templates import TextTemplateServiceProtocol, TextTemplateService
from ..categories.use_cases.categories.create_default import CreateDefaultCategoriesUseCaseProtocol
from ..categories.services.visibility_notifications import CheckVisibilityNotificationsServiceProtocol
from ..categories.depends import get_categories_create_default_use_case
from ..categories.depends_shared import get_check_visibility_notificaion_service, __get_check_visibility_notificaion_repository
from ...core.db import get_async_session, AsyncSession
from ...core.redis import get_redis_client
from ...core.depends import get_decode_token
from ...settings import Settings, get_settings
from .repositories.ignore import IgnoreRepository, IgnoreRepositoryProtocol
from .repositories.settings import ChatSettingsRepository, ChatSettingsRepositoryProtocol
from .repositories.messages import MessageRepository, MessageRepositoryProtocol
from .repositories.chat_history import ChatHistoryRepository, ChatHistoryRepositoryProtocol
from .repositories.bells import FavoriteBellsRepositoryProtocol, FavoriteBellsRepository
from .adapter.locations import LocationsServiceClient, LocationsServiceClientProtocol
from .adapter.characters import CharacterServiceClient, CharacterServiceClientProtocol
from .events.subscriber import RedisSubscriber, RedisSubscriberProtocol
from .events.character_event_handlers import CharacterEventHandler, CharacterEventHandlerProtocol
from .events.item_event_handlers import ItemEventHandler, ItemEventHandlerProtocol
from .events.mining_event_handlers import MiningEventHandler, MiningEventHandlerProtocol
from .events.monster_event_handlers import MonsterEventHandler, MonsterEventHandlerProtocol 
from .events.deal_event_handlers import DealEventHandler, DealEventHandlerProtocol
from .events.house_event_handlers import HouseEventHandler, HouseEventHandlerProtocol
from .events.rest_event_handlers import RestEventHandler, RestEventHandlerProtocol
from .services.ignore import (
    IgnoreService, IgnoreServiceProtocol,
    RateLimitIgnoreService, RateLimitIgnoreServiceProtocol
)
from .services.filters import (
    FilterProtocol, FilterLinks, FilterSmylies
)
from .services.settings import ChatSettingsService, ChatSettingsServiceProtocol
from .services.messages import (
    MessageService, MessageServiceProtocol, SendAndPublishMessageService
)
from .services.chat_history import ChatHistoryService, ChatHistoryServiceProtocol
from .services.publisher import RedisPublisher, RedisPublisherProtocol
from .services.room_checker import RoomChecker, RoomCheckerProtocol
from .services.rate_limit import RateLimitService, RateLimitServiceProtocol
from .services.bells import FavoriteBellsServiceProtocol, FavoriteBellsService
from .manager.websocket import WebSocketManager, WebSocketManagerProtocol, get_connection_registry
from .use_cases.ignore.create import CreateIgnoreUseCase, CreateIgnoreUseCaseProtocol
from .use_cases.ignore.delete import DeleteIgnoreUseCase, DeleteIgnoreUseCaseProtocol
from .use_cases.chat_settings.create_default import CreateDefaultSettingsUseCase, CreateDefaultSettingsUseCaseProtocol
from .use_cases.chat_settings.create_default_chat import CreateDefaultChatUseCase
from .use_cases.chat_settings.get_for_me import GetMeChatSettingsUseCase, GetMeChatSettingsUseCaseProtocol
from .use_cases.chat_settings.update import UpdateChatSettingsUseCase, UpdateChatSettingsUseCaseProtocol
from .use_cases.chat.send_message import SendMessageUseCase, SendMessageUseCaseProtocol
from .use_cases.chat.send_system_message import SendSystemMessageUseCase, SendSystemMessageUseCaseProtocol
from .use_cases.chat.valid_room import ValidRoomUseCase, ValidRoomUseCaseProtocol
from .use_cases.chat.valid_token import ValidTokenUseCase, ValidTokenUseCaseProtocol
from .use_cases.chat.validate import ValidateConnect, ValidateConnectProtocol
from .use_cases.chat.rate_limit import RateLimitUseCase, RateLimitUseCaseProtocol
from .use_cases.chat.get_history import GetChatHistoryUseCase, GetChatHistoryUseCaseProtocol
from .use_cases.bells.create import CreateFavoriteBellsUseCase, CreateFavoriteBellsUseCaseProtocol
from .use_cases.bells.delete import DeleteFavoriteBellsUseCase, DeleteFavoriteBellsUseCaseProtocol
from .use_cases.bells.get_all_for_character import GetAllFavoriteBellsForCharacterUseCase, GetAllFavoriteBellsForCharacterUseCaseProtocol
from .use_cases.characters.get_online_characters import GetOnlineCharactersUseCase, GetOnlineCharactersUseCaseProtocol
from .use_cases.chat.send_default_messages import SendDefaultMessagesUseCase, SendDefaultMessagesUseCaseProtocol
from .use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol
from .depends_shared import get_character_adapter, get_valid_status_character_use_case

_text_template_service: TextTemplateServiceProtocol = None

def get_text_template_service() -> TextTemplateServiceProtocol:
    return _text_template_service

def init_text_template_service(file_path: str):
    global _text_template_service
    _text_template_service = TextTemplateService(file_path)
    
# filters
def get_filters(settings: Settings = Depends(get_settings)) -> list[FilterProtocol]:
    return [
        FilterSmylies(max_smiles=settings.filter_smyles.max_smyles),
        FilterLinks(const_allowed_hosts=settings.filter_links.allowed_hosts,
                    frontend_url=settings.frontend_url)
    ]

# ignore
def get_rate_limit_ignore_service(
        redis: redis.Redis = Depends(get_redis_client)
) -> RateLimitIgnoreServiceProtocol:
    return RateLimitIgnoreService(redis)

def __get_ignore_repository(
    session: AsyncSession = Depends(get_async_session)
) -> IgnoreRepositoryProtocol:
    return IgnoreRepository(session)

def get_ignore_service(
    repository: IgnoreRepositoryProtocol = Depends(__get_ignore_repository),
    rate_limit_ignore_service: RateLimitIgnoreServiceProtocol = Depends(get_rate_limit_ignore_service)
) -> IgnoreServiceProtocol:
    return IgnoreService(repository, rate_limit_ignore_service)

# chat settings
def __get_chat_settings_repository(
    session: AsyncSession = Depends(get_async_session)
) -> ChatSettingsRepositoryProtocol:
    return ChatSettingsRepository(session)

def get_chat_settings_service(
    repository: ChatSettingsRepositoryProtocol = Depends(__get_chat_settings_repository)
) -> ChatSettingsServiceProtocol:
    return ChatSettingsService(repository)

def get_create_default_settings_use_case(
    service: ChatSettingsServiceProtocol = Depends(get_chat_settings_service)
) -> CreateDefaultSettingsUseCaseProtocol:
    return CreateDefaultSettingsUseCase(service)

# Message
def __get_message_repository(session: AsyncSession = Depends(get_async_session)) -> MessageRepositoryProtocol:
    return MessageRepository(session)

def get_location_adapter(settings: Settings = Depends(get_settings)) -> LocationsServiceClientProtocol:
    return LocationsServiceClient(base_url=settings.character_service_app.base_url)


def get_profanities() -> list[UniversalProfanity]:
    return [UniversalProfanity(country='en', replace_chars='*'),
            UniversalProfanity(country='ru', replace_chars='*')]

def get_message_service(repository: MessageRepositoryProtocol = Depends(__get_message_repository),
                        chat_settings_service: ChatSettingsServiceProtocol = Depends(get_chat_settings_service),
                        character_adapter: CharacterServiceClientProtocol = Depends(get_character_adapter),
                        profanities: list[UniversalProfanity] = Depends(get_profanities),
                        filters: list[FilterProtocol] = Depends(get_filters)
                        ) -> MessageServiceProtocol:
    return MessageService(repository, chat_settings_service, character_adapter, profanities, filters)


def get_room_checker_service(location_adapter: LocationsServiceClientProtocol = Depends(get_location_adapter),
                             settings: Settings = Depends(get_settings)) -> RoomCheckerProtocol:
    return RoomChecker(location_adapter, settings.valid_rooms)

def get_redis_publisher(redis_client: redis.Redis = Depends(get_redis_client)) -> RedisPublisherProtocol:
    return RedisPublisher(redis_client)


def get_send_and_publish_message_service(
        message_service: MessageServiceProtocol = Depends(get_message_service),
        publisher: RedisPublisherProtocol = Depends(get_redis_publisher)
) -> MessageServiceProtocol:
    return SendAndPublishMessageService(message_service, publisher)

def get_redis_subscriber(redis_client: redis.Redis = Depends(get_redis_client)) -> RedisSubscriberProtocol:
    return RedisSubscriber(redis_client)

def get_message_service_factory():
    def factory(session: AsyncSession):
        settings = get_settings()
        message_repository = __get_message_repository(session)
        character_adapter = get_character_adapter(settings)
        return get_message_service(
            repository=message_repository,
            chat_settings_service=None,
            character_adapter=character_adapter,
            profanities=[],
            filters=[]
        )
    return factory

def get_visibility_service_factory():
    def factory(session: AsyncSession):
        notification_repository = __get_check_visibility_notificaion_repository(session)
        return get_check_visibility_notificaion_service(notification_repository)
    return factory

def get_send_and_publish_message_service_factory():
    def factory(session: AsyncSession):
        message_service = get_message_service_factory()(session)
        redis_client = get_redis_client()
        redis_publisher = get_redis_publisher(redis_client)
        return SendAndPublishMessageService(message_service, redis_publisher)
    return factory

def get_character_handler(
    redis_subscriber: RedisSubscriberProtocol = Depends(get_redis_subscriber),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
    template_service: TextTemplateServiceProtocol = Depends(get_text_template_service),
    message_service_factory: Callable[[AsyncSession], MessageServiceProtocol] = Depends(get_send_and_publish_message_service_factory),
    visibility_service_factory: Callable[[AsyncSession], CheckVisibilityNotificationsServiceProtocol] = Depends(get_visibility_service_factory)
) -> CharacterEventHandlerProtocol:
    return CharacterEventHandler(
        redis_subscriber,
        redis_publisher,
        template_service,
        message_service_factory,
        visibility_service_factory
    )

def get_mining_handler(redis_subscriber: RedisSubscriberProtocol = Depends(get_redis_subscriber),
    message_service_factory: Callable[[AsyncSession], MessageServiceProtocol] = Depends(get_send_and_publish_message_service_factory),
    template_service: TextTemplateServiceProtocol = Depends(get_text_template_service)
) -> MiningEventHandlerProtocol:
    
    return MiningEventHandler(redis_subscriber, message_service_factory, template_service)

def get_items_handler(
    redis_subscriber: RedisSubscriberProtocol = Depends(get_redis_subscriber),
    message_service_factory: Callable[[AsyncSession], MessageServiceProtocol] = Depends(get_send_and_publish_message_service_factory),
    character_service: CharacterServiceClientProtocol = Depends(get_character_adapter),  # ← ДОБАВИТЬ
) -> ItemEventHandlerProtocol:
    return ItemEventHandler(redis_subscriber, message_service_factory, character_service)  # ← ДОБАВИТЬ ПАРАМЕТР

def get_monster_attack_handler(redis_subscriber: RedisSubscriberProtocol = Depends(get_redis_subscriber),
    message_service_factory: Callable[[AsyncSession], MessageServiceProtocol] = Depends(get_send_and_publish_message_service_factory),
    template_service: TextTemplateServiceProtocol = Depends(get_text_template_service)
    ) -> MonsterEventHandlerProtocol:
   
    return MonsterEventHandler(redis_subscriber, message_service_factory, template_service)

def get_ws_manager(redis_client: redis.Redis = Depends(get_redis_client),
                   ignore_service: IgnoreServiceProtocol = Depends(get_ignore_service),
                   chat_settings_service: ChatSettingsServiceProtocol = Depends(get_chat_settings_service),
                   visibility_checker: CheckVisibilityNotificationsServiceProtocol = Depends(get_check_visibility_notificaion_service)) -> WebSocketManagerProtocol:
    # Реестр соединений общий на процесс — иначе dedup не видит
    # подключения других сокетов и сообщения доставляются дважды.
    return WebSocketManager(redis_client, ignore_service, chat_settings_service, visibility_checker,
                            registry=get_connection_registry())

def get_deals_handler(
    redis_subscriber: RedisSubscriberProtocol,
    redis_publisher: RedisPublisherProtocol,
    message_service_factory: Callable[[AsyncSession], MessageServiceProtocol],
    template_service: TextTemplateServiceProtocol,
) -> DealEventHandlerProtocol:
    return DealEventHandler(
        redis_subscriber,
        redis_publisher,
        message_service_factory,
        template_service,
    )

def get_house_handler(
    redis_subscriber: RedisSubscriberProtocol,
    redis_publisher: RedisPublisherProtocol,
) -> HouseEventHandlerProtocol:
    return HouseEventHandler(redis_subscriber, redis_publisher)

def get_rest_handler(
    redis_subscriber: RedisSubscriberProtocol,
    redis_publisher: RedisPublisherProtocol,
) -> RestEventHandlerProtocol:
    return RestEventHandler(redis_subscriber, redis_publisher)


def get_validate_room_use_case(room_checker: RoomCheckerProtocol = Depends(get_room_checker_service)) -> ValidRoomUseCaseProtocol:
    return ValidRoomUseCase(room_checker)

def get_validate_token_use_case(decoder: DecodeAccessTokenProtocol = Depends(get_decode_token)) -> ValidTokenUseCaseProtocol:
    return ValidTokenUseCase(decoder)

def get_validate_connect_use_case(
        room_validator: ValidRoomUseCaseProtocol = Depends(get_validate_room_use_case),
        token_validator: ValidTokenUseCaseProtocol = Depends(get_validate_token_use_case)
) -> ValidateConnectProtocol:
    return ValidateConnect(token_validator, room_validator)

def get_send_message_use_case(message_service: MessageServiceProtocol = Depends(get_send_and_publish_message_service)) -> SendMessageUseCaseProtocol:
    return SendMessageUseCase(message_service)

def get_send_system_message_use_case(message_service: MessageServiceProtocol = Depends(get_send_and_publish_message_service)) -> SendSystemMessageUseCaseProtocol:
    return SendSystemMessageUseCase(message_service)

def get_rate_limit_service(redis_client: redis.Redis = Depends(get_redis_client),
                           settings: Settings = Depends(get_settings)) -> RateLimitServiceProtocol:
    return RateLimitService(redis_client, cooldown=settings.cooldown)

def get_rate_limit_use_case(rate_limiter: RateLimitServiceProtocol = Depends(get_rate_limit_service)) -> RateLimitUseCaseProtocol:
    return RateLimitUseCase(rate_limiter)

# Chart history
def __get_chat_history_repository(session: AsyncSession = Depends(get_async_session)) -> ChatHistoryRepositoryProtocol:
    return ChatHistoryRepository(session)

def get_chat_history_service(repository: ChatHistoryRepositoryProtocol = Depends(__get_chat_history_repository)) -> CharacterServiceClientProtocol:
    return ChatHistoryService(repository)

def get_chat_history_use_case(
        room_validator: ValidRoomUseCaseProtocol = Depends(get_validate_room_use_case),
        service: ChatHistoryServiceProtocol = Depends(get_chat_history_service),
        characters_service: CharacterServiceClientProtocol = Depends(get_character_adapter),
        ) -> GetChatHistoryUseCaseProtocol:
    return GetChatHistoryUseCase(room_validator, service, characters_service)

# ignore use cases
def get_create_ignore_use_case(
    service: IgnoreServiceProtocol = Depends(get_ignore_service),
    send_system_msg: SendSystemMessageUseCaseProtocol = Depends(get_send_system_message_use_case),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> CreateIgnoreUseCaseProtocol:
    return CreateIgnoreUseCase(service, send_system_msg, valid_or_raise)

def get_delete_ignore_use_case(
    service: IgnoreServiceProtocol = Depends(get_ignore_service),
    send_system_msg: SendSystemMessageUseCaseProtocol = Depends(get_send_system_message_use_case),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> DeleteIgnoreUseCaseProtocol:
    return DeleteIgnoreUseCase(service, send_system_msg, valid_or_raise)

# favorite bells
def __get_favorite_bells_repository(session: AsyncSession = Depends(get_async_session)) -> FavoriteBellsRepositoryProtocol:
    return FavoriteBellsRepository(session)

def get_favorite_bells_service(repository: FavoriteBellsRepositoryProtocol = Depends(__get_favorite_bells_repository)) -> FavoriteBellsServiceProtocol:
    return FavoriteBellsService(repository)

def get_create_favorite_bells_use_case(service: FavoriteBellsServiceProtocol = Depends(get_favorite_bells_service)) -> CreateFavoriteBellsUseCaseProtocol:
    return CreateFavoriteBellsUseCase(service)

def get_delete_favorite_bells_use_case(service: FavoriteBellsServiceProtocol = Depends(get_favorite_bells_service)) -> DeleteFavoriteBellsUseCaseProtocol:
    return DeleteFavoriteBellsUseCase(service)

def get_get_all_for_character_use_case(service: FavoriteBellsServiceProtocol = Depends(get_favorite_bells_service)) -> GetAllFavoriteBellsForCharacterUseCaseProtocol:
    return GetAllFavoriteBellsForCharacterUseCase(service)

# characters
def get_get_online_characters_use_case(
        ignore_service: IgnoreServiceProtocol = Depends(get_ignore_service),
        characters_service: CharacterServiceClient = Depends(get_character_adapter)
        ) -> GetOnlineCharactersUseCaseProtocol:
    return GetOnlineCharactersUseCase(ignore_service, characters_service)

# send default messages
def get_send_default_messages(send_system_msg: SendSystemMessageUseCaseProtocol = Depends(get_send_system_message_use_case),
                              template_service: TextTemplateServiceProtocol = Depends(get_text_template_service),
                              settings: Settings = Depends(get_settings)) -> SendDefaultMessagesUseCaseProtocol:
    return SendDefaultMessagesUseCase(send_system_msg, template_service, settings.frontend_url)

def get_create_default_chat_use_case(
        create_default_settings: CreateDefaultSettingsUseCaseProtocol = Depends(get_create_default_settings_use_case),
        create_default_categories: CreateDefaultCategoriesUseCaseProtocol = Depends(get_categories_create_default_use_case),
        send_default_messages: SendDefaultMessagesUseCaseProtocol = Depends(get_send_default_messages)
) -> CreateDefaultSettingsUseCaseProtocol:
    return CreateDefaultChatUseCase(create_default_settings, create_default_categories, send_default_messages)

def get_get_my_settings_use_case(
    service: ChatSettingsServiceProtocol = Depends(get_chat_settings_service)
) -> GetMeChatSettingsUseCaseProtocol:
    return GetMeChatSettingsUseCase(service)

def get_update_settings_use_case(
    service: ChatSettingsServiceProtocol = Depends(get_chat_settings_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> UpdateChatSettingsUseCaseProtocol:
    return UpdateChatSettingsUseCase(service, valid_or_raise)
