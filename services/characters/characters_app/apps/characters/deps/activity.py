from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ....settings import Settings, get_settings
from ..repositories.activity.activity import (
    CharacterActivityRepositoryProtocol,
    CharacterActivityRepository,
)
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..services.activity.activity import (
    CharacterActivityServiceProtocol,
    CharacterActivityService,
    CharacterActivityWithUpdateStatusServiceProtocol,
    CharacterActivityWithUpdateStatusService,
    CharacterStatusChangerProtocol,
    CharacterStatusChanger,
    CleanupOldActivityServiceProtocol,
    CleanupOldActivityService,
)
from ..services.character.characters import (
    UpdateCharacterStatusServiceProtocol,
    UpdateCharacterStatusService,
)
from ..use_cases.activity.change_inactive import (
    ChangeStatusCharacterUseCaseProtocol,
    ChangeStatusCharacterUseCase,
)
from ..use_cases.activity.cleanup import (
    CleanupActivityUseCaseProtocol,
    CleanupActivityUseCase,
)
from ...rest.services.house_guest_service import HouseGuestServiceProtocol
from ...rest.depends import get_house_guest_service
from .character import get_update_character_status_service
from .valid import __get_character_repository


def __get_character_activity_repository(session: AsyncSession = Depends(get_async_session), settings: Settings = Depends(get_settings)) -> CharacterActivityRepository:
    return CharacterActivityRepository(session=session,
                                       inactive_minutes=settings.character_settings.inactive_time_minutes,
                                       delete_after_minutes=settings.character_activity_settings.delete_after_minutes)


def get_character_activity_service(repository: CharacterActivityRepositoryProtocol = Depends(__get_character_activity_repository)) -> CharacterActivityServiceProtocol:
    return CharacterActivityService(repository=repository)


def get_character_activity_with_status_service(character_activity_service: CharacterActivityServiceProtocol = Depends(get_character_activity_service),
                                               character_update: UpdateCharacterStatusServiceProtocol = Depends(get_update_character_status_service)) -> CharacterActivityWithUpdateStatusServiceProtocol:
    return CharacterActivityWithUpdateStatusService(activity_service=character_activity_service, character_update=character_update)


def get_character_status_changer(activity_repository: CharacterActivityRepositoryProtocol = Depends(__get_character_activity_repository),
                                 character_update: UpdateCharacterStatusServiceProtocol = Depends(get_update_character_status_service)) -> CharacterStatusChangerProtocol:
    return CharacterStatusChanger(character_repository=activity_repository,
                                  character_update=character_update)


def get_cleanup_character_activity_service(activity_repository: CharacterActivityRepositoryProtocol = Depends(__get_character_activity_repository)) -> CleanupOldActivityServiceProtocol:
    return CleanupOldActivityService(repository=activity_repository)


def get_change_inactive_use_case(
    session: AsyncSession,
    settings: Settings,
    house_guest_service: HouseGuestServiceProtocol,
) -> ChangeStatusCharacterUseCaseProtocol:
    activity_repo = __get_character_activity_repository(session=session, settings=settings)
    character_repo = __get_character_repository(session=session)
    character_update = get_update_character_status_service(
        repository=character_repo,
        house_guest_service=house_guest_service,
    )
    character_status_changer = get_character_status_changer(
        activity_repository=activity_repo,
        character_update=character_update,
    )
    return ChangeStatusCharacterUseCase(character_status_changer)

def get_change_inactive_use_case_factory(
    session: AsyncSession,
    settings: Settings,
    redis_client,
    house_guest_service: HouseGuestServiceProtocol,
) -> ChangeStatusCharacterUseCaseProtocol:
    """Factory для Celery tasks - создаёт publisher с локальным redis"""
    activity_repo = __get_character_activity_repository(session=session, settings=settings)
    character_repo = __get_character_repository(session=session)

    # Создаём RedisPublisher вручную, а не через Depends
    from ....core.redis import RedisPublisher
    publisher = RedisPublisher(redis_client=redis_client)

    character_update = UpdateCharacterStatusService(
        repository=character_repo,
        publisher=publisher,
        house_guest_service=house_guest_service,
    )
    character_status_changer = get_character_status_changer(
        activity_repository=activity_repo,
        character_update=character_update,
    )
    return ChangeStatusCharacterUseCase(character_status_changer)


def get_cleanup_acitvity_use_case(session: AsyncSession, settings: Settings) -> CleanupActivityUseCaseProtocol:
    activity_repo = __get_character_activity_repository(session=session, settings=settings)
    activity_service = get_cleanup_character_activity_service(activity_repo)
    return CleanupActivityUseCase(activity_service)
