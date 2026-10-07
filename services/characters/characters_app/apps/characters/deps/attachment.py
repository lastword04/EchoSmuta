from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ....settings import Settings, get_settings
from ..repositories.attachment.character_attachment_settings import (
    CharacterAttachmentSettingsRepositoryProtocol,
    CharacterAttachmentSettingsRepository,
)
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..services.attachment.character_attachment_service import (
    CharacterAttachmentSettingsServiceProtocol,
    CharacterAttachmentSettingsService,
)
from ..services.character.characters import (
    CharacterAttachmentServiceProtocol,
    CharacterAttachmentService,
    CharacterCleanupServiceProtocol,
    CharacterCleanupService,
)
from ..services.settings.user_character_settings import UserCharacterSettingsServiceProtocol
from ..use_cases.attachment.cleanup_all_detached import (
    CleanupDetachedCharactersUseCaseProtocol,
    CleanupDetachedCharactersUseCase,
)
from ..use_cases.attachment.attach_character import (
    AttachCharacterUseCaseProtocol,
    AttachCharacterUseCase,
)
from ..use_cases.attachment.detach_character import (
    DetachCharacterUseCaseProtocol,
    DetachCharacterUseCase,
)
from ..use_cases.attachment.get_detached_characters import (
    GetDetachCharacterStatusUseCaseProtocol,
    GetDetachCharacterStatusUseCase,
)
from ..use_cases.attachment.has_detach_characters import (
    HasDetachCharacterStatusUseCaseProtocol,
    HasDetachCharacterStatusUseCase,
)
from ..use_cases.initializators.init_character_attachment_settings import (
    InitializeCharacterAttachmentSettingsUseCaseProtocol,
    InitializeCharacterAttachmentSettingsUseCase,
)
from ..use_cases.attachment.get_character_attachment_settings import (
    GetCharacterAttachmentSettingsUseCaseProtocol,
    GetCharacterAttachmentSettingsUseCase,
)
from .settings import get_user_character_settings_service_dep
from .valid import __get_character_repository


def __get_character_attachment_settings_repository_dep(session: AsyncSession = Depends(get_async_session)) -> CharacterAttachmentSettingsRepositoryProtocol:
    return CharacterAttachmentSettingsRepository(session=session)


def get_character_attachment_settings_service_dep(repository: CharacterAttachmentSettingsRepositoryProtocol = Depends(__get_character_attachment_settings_repository_dep)) -> CharacterAttachmentSettingsServiceProtocol:
    return CharacterAttachmentSettingsService(repository=repository)


def get_initialize_character_attachment_settings_use_case_dep(session: AsyncSession) -> InitializeCharacterAttachmentSettingsUseCaseProtocol:
    repo = __get_character_attachment_settings_repository_dep(session=session)
    service = get_character_attachment_settings_service_dep(repository=repo)
    return InitializeCharacterAttachmentSettingsUseCase(service=service)


def get_character_attachment_settings_use_case_dep(service: CharacterAttachmentSettingsServiceProtocol = Depends(get_character_attachment_settings_service_dep)) -> GetCharacterAttachmentSettingsUseCaseProtocol:
    return GetCharacterAttachmentSettingsUseCase(service=service)

def get_character_attachment_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
                                     user_character_settings_service: UserCharacterSettingsServiceProtocol = Depends(get_user_character_settings_service_dep),
                                     character_attachment_settings_service: CharacterAttachmentSettingsServiceProtocol = Depends(get_character_attachment_settings_service_dep),
                                     settings: Settings = Depends(get_settings)) -> CharacterAttachmentServiceProtocol:
    return CharacterAttachmentService(repository=repository, user_character_settings_service=user_character_settings_service,
                                      character_attachment_settings_service=character_attachment_settings_service,
                                      period_deletion_days=settings.character_settings.deactivation_period_days
                                      )


def get_detach_character_use_case(service: CharacterAttachmentServiceProtocol = Depends(get_character_attachment_service)) -> DetachCharacterUseCaseProtocol:
    return DetachCharacterUseCase(service=service)


def get_attach_character_use_case(service: CharacterAttachmentServiceProtocol = Depends(get_character_attachment_service)) -> AttachCharacterUseCaseProtocol:
    return AttachCharacterUseCase(service=service)


def get_has_detach_character_status_use_case(service: CharacterAttachmentServiceProtocol = Depends(get_character_attachment_service)) -> HasDetachCharacterStatusUseCaseProtocol:
    return HasDetachCharacterStatusUseCase(service=service)


def get_get_detached_characters_use_case(service: CharacterAttachmentServiceProtocol = Depends(get_character_attachment_service)) -> GetDetachCharacterStatusUseCaseProtocol:
    return GetDetachCharacterStatusUseCase(service=service)


def get_cleanup_detached_service(
        repository: CharacterRepositoryProtocol = Depends(__get_character_repository)
                                 ) -> CharacterCleanupServiceProtocol:
    return CharacterCleanupService(repository=repository)


def get_cleanup_detached_characters_use_case(
        session: AsyncSession
) -> CleanupDetachedCharactersUseCaseProtocol:
    repo = __get_character_repository(session=session)
    service = get_cleanup_detached_service(repository=repo)
    return CleanupDetachedCharactersUseCase(service=service)
