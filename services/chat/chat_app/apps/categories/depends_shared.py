from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from .repositories.block_characters import CheckSendMailRepositoryProtocol, CheckSendMailRepository
from .repositories.visibility_notifications import CheckVisibilityNotificationsRepositoryProtocol, CheckVisibilityNotificationsRepository
from .services.block_characters import CheckSendMailServiceProtocol, CheckSendMailService
from .services.visibility_notifications import CheckVisibilityNotificationsServiceProtocol, CheckVisibilityNotificationsService

def __get_check_send_mail_repository(session: AsyncSession = Depends(get_async_session)) -> CheckSendMailRepositoryProtocol:
    return CheckSendMailRepository(session)

def get_check_send_mail_service(repository: CheckSendMailRepositoryProtocol = Depends(__get_check_send_mail_repository)) -> CheckSendMailServiceProtocol:
    return CheckSendMailService(repository)

def __get_check_visibility_notificaion_repository(session: AsyncSession = Depends(get_async_session)) -> CheckVisibilityNotificationsRepositoryProtocol:
    return CheckVisibilityNotificationsRepository(session)

def get_check_visibility_notificaion_service(repository: CheckVisibilityNotificationsRepositoryProtocol = Depends(__get_check_visibility_notificaion_repository)) -> CheckVisibilityNotificationsServiceProtocol:
    return CheckVisibilityNotificationsService(repository)

