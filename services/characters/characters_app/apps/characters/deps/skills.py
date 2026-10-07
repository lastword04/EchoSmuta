from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ...stats.depends import get_stats_publisher
from ...stats.services.publisher.stats_publisher import StatsPublisher
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..repositories.skills.character_ability_skills import (
    CharacterAbilitySkillsRepositoryProtocol,
    CharacterAbilitySkillsRepository,
)
from ..repositories.skills.applied_character_history import (
    AppliedCharacterHistoryRepositoryProtocol,
    AppliedCharacterHistoryRepository,
)
from ..repositories.skills.character_distributions import (
    CharacterDistributionsRepositoryProtocol,
    CharacterDistributionsRepository,
)
from ..services.skills.character_ability_skills import (
    CharacterAbilitySkillsServiceProtocol,
    CharacterAbilitySkillsService,
)
from ..services.skills.applied_character_history import (
    AppliedCharacterHistoryServiceProtocol,
    AppliedCharacterHistoryService,
)
from ..services.skills.character_distributions import (
    CharacterDistributionsServiceProtocol,
    CharacterDistributionsService,
)
from ..services.skills.reset_character_distributions import (
    ResetCharacterDistributionsServiceProtocol,
    ResetCharacterDistributionsService,
)
from ..use_cases.skills.get_applied_skills_by_character import (
    AppliedCharacterHistoryUseCaseProtocol,
    AppliedCharacterHistoryUseCase,
)
from ..use_cases.skills.get_ability_by_character import (
    GetMyCharacterAbilitySkillsUseCaseProtocol,
    GetMyCharacterAbilitySkillsUseCase,
)
from ..use_cases.skills.recalculate_equipment_bonuses import (
    RecalculateEquipmentBonusesUseCase,
    RecalculateEquipmentBonusesUseCaseProtocol,
)
from .valid import __get_character_repository


def __get_character_ability_skills_repository(session: AsyncSession = Depends(get_async_session)
) -> CharacterAbilitySkillsRepositoryProtocol:
    return CharacterAbilitySkillsRepository(session=session)


def get_character_ability_skills_service(repository: CharacterAbilitySkillsRepositoryProtocol = Depends(__get_character_ability_skills_repository)
) -> CharacterAbilitySkillsServiceProtocol:
    return CharacterAbilitySkillsService(repository=repository)


def get_get_ability_by_character(service: CharacterAbilitySkillsServiceProtocol = Depends(get_character_ability_skills_service)) -> GetMyCharacterAbilitySkillsUseCaseProtocol:
    return GetMyCharacterAbilitySkillsUseCase(service)


def __get_applied_character_history_repository(session: AsyncSession = Depends(get_async_session)
) -> AppliedCharacterHistoryRepositoryProtocol:
    return AppliedCharacterHistoryRepository(session=session)


def get_applied_character_history_service(repository: AppliedCharacterHistoryRepositoryProtocol = Depends(__get_applied_character_history_repository)
) -> AppliedCharacterHistoryServiceProtocol:
    return AppliedCharacterHistoryService(repository=repository)


def __get_character_distributions_repository(session: AsyncSession = Depends(get_async_session)
) -> CharacterDistributionsRepositoryProtocol:
    return CharacterDistributionsRepository(session=session)


def get_character_distributions_service(repository: AppliedCharacterHistoryRepositoryProtocol = Depends(__get_character_distributions_repository)
) -> CharacterDistributionsServiceProtocol:
    return CharacterDistributionsService(repository=repository)


def get_get_applied_skills_by_character(history_service: AppliedCharacterHistoryServiceProtocol = Depends(get_applied_character_history_service),
distribution_service: CharacterDistributionsServiceProtocol = Depends(get_character_distributions_service)
) -> AppliedCharacterHistoryUseCaseProtocol:
    return AppliedCharacterHistoryUseCase(history_service, distribution_service)


def get_reset_character_distributions_service(repository: CharacterDistributionsRepositoryProtocol = Depends(__get_character_distributions_repository)
) -> ResetCharacterDistributionsServiceProtocol:
    return ResetCharacterDistributionsService(repository=repository)


def get_recalculate_equipment_bonuses_use_case(
    character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
    publisher: StatsPublisher = Depends(get_stats_publisher),
) -> RecalculateEquipmentBonusesUseCaseProtocol:
    """Функция для получения use case пересчёта бонусов экипировки."""
    return RecalculateEquipmentBonusesUseCase(
        character_repository=character_repository,
        publisher=publisher,
    )
