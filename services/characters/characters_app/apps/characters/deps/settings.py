from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.settings.race_settings import (
    RaceSettingsRepositoryProtocol,
    RaceSettingsRepository,
)
from ..repositories.settings.global_settings import (
    GlobalCharacterSettingsRepositoryProtocol,
    GlobalCharacterSettingsRepository,
)
from ..repositories.settings.experience_settings import (
    GlobalCharacterExperienceSettingsRepositoryProtocol,
    GlobalCharacterExperienceSettingsRepository,
)
from ..repositories.settings.user_character_settings import (
    UserCharacterSettingsRepositoryProtocol,
    UserCharacterSettingsRepository,
)
from ..services.settings.race_settings import (
    RaceSettingsServiceProtocol,
    RaceSettingsService,
)
from ..services.settings.global_settings import (
    GlobalCharacterSettingsServiceProtocol,
    GlobalCharacterSettingsService,
)
from ..services.settings.experience_settings import (
    GlobalCharacterExperienceSettingsServiceProtocol,
    GlobalCharacterExperienceSettingsService,
)
from ..services.settings.user_character_settings import (
    UserCharacterSettingsServiceProtocol,
    UserCharacterSettingsService,
)
from ..use_cases.initializators.init_race_settings import (
    InitializeRaceSettingsUseCaseProtocol,
    InitializeRaceSettingsUseCase,
)
from ..use_cases.initializators.init_global_settings import (
    InitializeGlobalCharacterSettingsUseCaseProtocol,
    InitializeGlobalCharacterSettingsUseCase,
)
from ..use_cases.initializators.init_experience_settings import (
    InitializeGlobalCharacterExperienceSettingsUseCaseProtocol,
    InitializeGlobalCharacterExperienceSettingsUseCase,
)


def __get_race_settings_repository(session: AsyncSession) -> RaceSettingsRepositoryProtocol:
    return RaceSettingsRepository(session=session)


def get_race_settings_service(session: AsyncSession) -> RaceSettingsServiceProtocol:
    repository = __get_race_settings_repository(session=session)
    return RaceSettingsService(repository=repository)


def get_initialize_race_settings_use_case(session: AsyncSession) -> InitializeRaceSettingsUseCaseProtocol:
    service = get_race_settings_service(session=session)
    return InitializeRaceSettingsUseCase(service=service)


def __get_global_character_settings_repository(session: AsyncSession) -> GlobalCharacterSettingsRepositoryProtocol:
    return GlobalCharacterSettingsRepository(session=session)


def get_global_character_settings_service(session: AsyncSession) -> GlobalCharacterSettingsServiceProtocol:
    repository = __get_global_character_settings_repository(session=session)
    return GlobalCharacterSettingsService(repository=repository)


def get_initialize_global_character_settings_use_case(session: AsyncSession) -> InitializeGlobalCharacterSettingsUseCaseProtocol:
    service = get_global_character_settings_service(session=session)
    return InitializeGlobalCharacterSettingsUseCase(service=service)


def __get_global_character_experience_settings_repository(session: AsyncSession = Depends(get_async_session)
) -> GlobalCharacterExperienceSettingsRepositoryProtocol:
    return GlobalCharacterExperienceSettingsRepository(session=session)


def get_global_character_experience_settings_service(repository: GlobalCharacterExperienceSettingsRepositoryProtocol = Depends(__get_global_character_experience_settings_repository)
) -> GlobalCharacterExperienceSettingsServiceProtocol:
    return GlobalCharacterExperienceSettingsService(repository=repository)


def get_initialize_global_character_experience_settings_use_case(session: AsyncSession = Depends(get_async_session)
    ) -> InitializeGlobalCharacterExperienceSettingsUseCaseProtocol:
    global_character_experience_settings_repository = __get_global_character_experience_settings_repository(session=session)
    global_character_experience_settings_service = get_global_character_experience_settings_service(repository=global_character_experience_settings_repository)
    return InitializeGlobalCharacterExperienceSettingsUseCase(service=global_character_experience_settings_service)


def __get_race_settings_repository_dep(session: AsyncSession = Depends(get_async_session)) -> RaceSettingsRepositoryProtocol:
    return RaceSettingsRepository(session=session)


def get_race_settings_service_dep(repository: RaceSettingsRepositoryProtocol = Depends(__get_race_settings_repository_dep)) -> RaceSettingsServiceProtocol:
    return RaceSettingsService(repository=repository)


def get_initialize_race_settings_use_case_dep(service: RaceSettingsServiceProtocol = Depends(get_race_settings_service_dep)) -> InitializeRaceSettingsUseCaseProtocol:
    return InitializeRaceSettingsUseCase(service=service)


def __get_global_character_settings_repository_dep(session: AsyncSession = Depends(get_async_session)) -> GlobalCharacterSettingsRepositoryProtocol:
    return GlobalCharacterSettingsRepository(session=session)


def get_global_character_settings_service_dep(repository: GlobalCharacterSettingsRepositoryProtocol = Depends(__get_global_character_settings_repository_dep)) -> GlobalCharacterSettingsServiceProtocol:
    return GlobalCharacterSettingsService(repository=repository)


def __get_user_character_settings_repository_dep(session: AsyncSession = Depends(get_async_session)) -> UserCharacterSettingsRepositoryProtocol:
    return UserCharacterSettingsRepository(session=session)


def get_user_character_settings_service_dep(repository: UserCharacterSettingsRepositoryProtocol = Depends(__get_user_character_settings_repository_dep)) -> UserCharacterSettingsServiceProtocol:
    return UserCharacterSettingsService(repository=repository)


def get_initialize_global_character_settings_use_case_dep(service: GlobalCharacterSettingsServiceProtocol = Depends(get_global_character_settings_service_dep)) -> InitializeGlobalCharacterSettingsUseCaseProtocol:
    return InitializeGlobalCharacterSettingsUseCase(service=service)
