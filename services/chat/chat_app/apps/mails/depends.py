from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from ...settings import Settings, get_settings
from ..messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol
from ..messages.depends_shared import get_valid_status_character_use_case
from ..categories.services.block_characters import CheckSendMailServiceProtocol
from ..categories.depends_shared import get_check_send_mail_service
from .adapters.characters import CharacterServiceClient, CharacterServiceClientProtocol
from .repositories.mail_messages import MailMessageRepository, MailMessageRepositoryProtocol
from .repositories.mail_recieve_settings import MailReceiveSettingsRepository, MailReceiveSettingsRepositoryProtocol
from .services.mail_messages import MailMessageService, MailMessageServiceProtocol
from .services.mail_recieve_settings import MailReceiveSettingsService, MailReceiveSettingsServiceProtocol
from .use_cases.create import CreateMailMessageUseCase, CreateMailMessageUseCaseProtocol
from .use_cases.delete import DeleteMailMessageUseCase, DeleteMailMessageUseCaseProtocol
from .use_cases.delete_for_sender import DeleteForSenderMailMessageUseCase, DeleteForSenderMailMessageUseCaseProtocol
from .use_cases.delete_for_recipient import DeleteForRecipientMailMessageUseCase, DeleteForRecipientMailMessageUseCaseProtocol
from .use_cases.get_for_me import GetMailMessageForMeUseCase, GetMailMessageForMeUseCaseProtocol
from .use_cases.get_my import GetMyMailMessageUseCase, GetMyMailMessageUseCaseProtocol
from .use_cases.update_all_messages_to_is_read import UpdateMailMessagesToIsReadUseCase, UpdateMailMessagesToIsReadUseCaseProtocol
from .use_cases.check_not_is_read_messages import CheckNotIsReadMessageUseCase, CheckNotIsReadMessageUseCaseProtocol 
from .use_cases.mails_settings.create import CreateMailsSettingsUseCase, CreateMailsSettingsUseCaseProtocol
from .use_cases.mails_settings.delete import DeleteMailsSettingsUseCase, DeleteMailsSettingsUseCaseProtocol
from .use_cases.mails_settings.get import GetMailsSettingsUseCase, GetMailsSettingsUseCaseProtocol
import redis.asyncio as redis
from ...core.redis import get_redis_client
from .events.publisher import RedisPublisherProtocol, RedisPublisher
from .events.mail_notifications import MailNotificationEventsProtocol, MailNotificationEvents

# mails settings
def __get_mails_settings_repository(session: AsyncSession = Depends(get_async_session)) -> MailReceiveSettingsRepositoryProtocol:
    return MailReceiveSettingsRepository(session)

def get_mails_settings_service(repository: MailMessageRepositoryProtocol = Depends(__get_mails_settings_repository)) -> MailReceiveSettingsServiceProtocol:
    return MailReceiveSettingsService(repository)

def get_get_mails_settings_use_case(service: MailReceiveSettingsServiceProtocol = Depends(get_mails_settings_service),
                                    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
                                    ) -> GetMailsSettingsUseCaseProtocol:
    return GetMailsSettingsUseCase(service, valid_or_raise)

def get_create_mails_settings_use_case(service: MailReceiveSettingsServiceProtocol = Depends(get_mails_settings_service),
                                       valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
                                       ) -> CreateMailsSettingsUseCaseProtocol:
    return CreateMailsSettingsUseCase(service, valid_or_raise)

def get_delete_mails_settings_use_case(service: MailReceiveSettingsServiceProtocol = Depends(get_mails_settings_service),
                                        valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
                                       ) -> DeleteMailsSettingsUseCaseProtocol:
    return DeleteMailsSettingsUseCase(service, valid_or_raise)

# mails
def get_mail_message_repository(
    session: AsyncSession = Depends(get_async_session),
) -> MailMessageRepositoryProtocol:
    return MailMessageRepository(session)

def get_character_service_client(
    settings: Settings = Depends(get_settings)
) -> CharacterServiceClientProtocol:
    return CharacterServiceClient(base_url=settings.character_service_app.base_url)

def get_redis_publisher(redis_client: redis.Redis = Depends(get_redis_client)) -> RedisPublisherProtocol:
    return RedisPublisher(redis_client)

def get_mail_notification_events(
    publisher: RedisPublisherProtocol = Depends(get_redis_publisher)
) -> MailNotificationEventsProtocol:
    return MailNotificationEvents(publisher)

def get_mail_message_service(
    repository: MailMessageRepositoryProtocol = Depends(get_mail_message_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    mails_settings: MailReceiveSettingsServiceProtocol = Depends(get_mails_settings_service),
    category_mail_checker: CheckSendMailServiceProtocol = Depends(get_check_send_mail_service),
    mail_events: MailNotificationEventsProtocol = Depends(get_mail_notification_events)
) -> MailMessageServiceProtocol:
    return MailMessageService(
        repository=repository,
        character_service=character_service,
        mails_settings=mails_settings,
        category_mail_checker=category_mail_checker,
        mail_events=mail_events
    )

def get_create_mail_message_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> CreateMailMessageUseCaseProtocol:
    return CreateMailMessageUseCase(service=service, valid_or_raise=valid_or_raise)

# def get_delete_mail_message_use_case(
#     service: MailMessageServiceProtocol = Depends(get_mail_message_service),
#     valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
# ) -> DeleteMailMessageUseCaseProtocol:
#     return DeleteMailMessageUseCase(service=service, valid_or_raise=valid_or_raise)

def get_delete_for_recipient_mail_message_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> DeleteForRecipientMailMessageUseCaseProtocol:
    return DeleteForRecipientMailMessageUseCase(service=service, valid_or_raise=valid_or_raise)


def get_delete_for_sender_mail_message_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> DeleteForSenderMailMessageUseCaseProtocol:
    return DeleteForSenderMailMessageUseCase(service=service, valid_or_raise=valid_or_raise)


def get_get_mail_message_for_me_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> GetMailMessageForMeUseCaseProtocol:
    return GetMailMessageForMeUseCase(service=service, valid_or_raise=valid_or_raise)

def get_get_my_mail_message_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> GetMyMailMessageUseCaseProtocol:
    return GetMyMailMessageUseCase(service=service, valid_or_raise=valid_or_raise)

def get_update_all_messages_to_is_read_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> UpdateMailMessagesToIsReadUseCaseProtocol:
    return UpdateMailMessagesToIsReadUseCase(service=service, valid_or_raise=valid_or_raise)

def get_check_not_is_read_message_use_case(
    service: MailMessageServiceProtocol = Depends(get_mail_message_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
) -> CheckNotIsReadMessageUseCaseProtocol:
    return CheckNotIsReadMessageUseCase(service=service, valid_or_raise=valid_or_raise)

