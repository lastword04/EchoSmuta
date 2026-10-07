from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from ...core.redis import get_redis_client
from .repositories.buff_repository import BuffRepository, BuffRepositoryProtocol
from .services.buff_service import BuffService, BuffServiceProtocol
from .services.collector.buffs import BuffsCollector
from .services.collector.equipment import EquipmentCollector
from .services.collector.modifiers import ModifiersCollector
from .services.publisher.stats_publisher import StatsPublisher
from .services.effective_stats import EffectiveStatsService
from .use_cases.apply_buff import ApplyBuffUseCase, ApplyBuffUseCaseProtocol
from .use_cases.remove_buff import RemoveBuffUseCase, RemoveBuffUseCaseProtocol
from .use_cases.get_buffs import GetCharacterBuffsUseCase, GetCharacterBuffsUseCaseProtocol
from .use_cases.passive_regeneration import PassiveRegenerationUseCase, PassiveRegenerationUseCaseProtocol
from .use_cases.consume_food import ConsumeFoodUseCase
from ..characters.repositories.character.characters import CharacterRepository, CharacterRepositoryProtocol



# Репозитории
def __get_buff_repository(
    session: AsyncSession = Depends(get_async_session)
) -> BuffRepositoryProtocol:
    return BuffRepository(session=session)


def __get_character_repository(
    session: AsyncSession = Depends(get_async_session)
) -> CharacterRepositoryProtocol:
    return CharacterRepository(session=session)


# Collector'ы
def get_buffs_collector(
    repository: BuffRepositoryProtocol = Depends(__get_buff_repository),
) -> BuffsCollector:
    return BuffsCollector(buff_repository=repository)


def get_equipment_collector() -> EquipmentCollector:
    return EquipmentCollector()


def get_modifiers_collector(
    equipment: EquipmentCollector = Depends(get_equipment_collector),
    buffs: BuffsCollector = Depends(get_buffs_collector),
) -> ModifiersCollector:
    return ModifiersCollector(collectors=[equipment, buffs])


# Publisher
def get_stats_publisher(
    character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
    modifiers_collector: ModifiersCollector = Depends(get_modifiers_collector),
    buffs_collector: BuffsCollector = Depends(get_buffs_collector),
    redis_client = Depends(get_redis_client),
) -> StatsPublisher:
    return StatsPublisher(
        redis_client=redis_client,
        character_repository=character_repository,
        modifiers_collector=modifiers_collector,
        buffs_collector=buffs_collector,
    )


# Сервис
def get_buff_service(
    repository: BuffRepositoryProtocol = Depends(__get_buff_repository),
    character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
    publisher: StatsPublisher = Depends(get_stats_publisher),
    collector: BuffsCollector = Depends(get_buffs_collector),
    modifiers_collector: ModifiersCollector = Depends(get_modifiers_collector),
) -> BuffServiceProtocol:
    return BuffService(
        repository=repository,
        character_repository=character_repository,
        publisher=publisher,
        collector=collector,
        modifiers_collector=modifiers_collector,
    )


# Use Cases
def get_apply_buff_use_case(
    service: BuffServiceProtocol = Depends(get_buff_service)
) -> ApplyBuffUseCaseProtocol:
    return ApplyBuffUseCase(service=service)


def get_remove_buff_use_case(
    service: BuffServiceProtocol = Depends(get_buff_service)
) -> RemoveBuffUseCaseProtocol:
    return RemoveBuffUseCase(service=service)


def get_character_buffs_use_case(
    service: BuffServiceProtocol = Depends(get_buff_service)
) -> GetCharacterBuffsUseCaseProtocol:
    return GetCharacterBuffsUseCase(service=service)


def get_passive_regeneration_use_case_factory(session: AsyncSession, redis_client) -> PassiveRegenerationUseCaseProtocol:
    """Factory для Celery tasks - создаёт новые экземпляры каждый раз"""
    character_repository = CharacterRepository(session=session)
    collector = BuffsCollector(buff_repository=BuffRepository(session=session))
    modifiers_collector = ModifiersCollector(
        collectors=[EquipmentCollector(), collector]
    )
    publisher = StatsPublisher(
        redis_client=redis_client,
        character_repository=character_repository,
        modifiers_collector=modifiers_collector,
        buffs_collector=collector,
    )
    return PassiveRegenerationUseCase(
        publisher=publisher,
        session=session,
    )


def get_character_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterRepositoryProtocol:
    return CharacterRepository(session=session)


def get_consume_food_use_case(
    buff_service: BuffService = Depends(get_buff_service),
    character_repository: CharacterRepositoryProtocol = Depends(get_character_repository),
) -> ConsumeFoodUseCase:
    return ConsumeFoodUseCase(buff_service, character_repository)