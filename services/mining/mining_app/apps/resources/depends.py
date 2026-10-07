from collections.abc import Callable
from typing import TYPE_CHECKING

import redis.asyncio as redis
from fastapi import Depends

from shared.services.templates import TextTemplateService, TextTemplateServiceProtocol

from ...core.db import AsyncSession, get_async_session
from ...core.redis import get_redis_client
from ...settings import Settings, get_settings
from .adapters.captcha import CaptchaServiceClient, CaptchaServiceClientProtocol
from .adapters.characters import CharacterServiceClient, CharacterServiceClientProtocol
from .repositories.character_resource import (
    CharacterResourceRepository,
    CharacterResourceRepositoryProtocol,
)
from .repositories.experience_for_level import (
    ExperienceForLevelRepository,
    ExperienceForLevelRepositoryProtocol,
)
from .repositories.location_character_expierence import (
    CharacterLocationStatsRepository,
    CharacterLocationStatsRepositoryProtocol,
)
from .repositories.location_resources import (
    LocationResourceRepository,
    LocationResourceRepositoryProtocol,
)
from .repositories.location_resources_character import (
    LocationResourcesCharacterRepository,
    LocationResourcesCharacterRepositoryProtocol,
)
from .repositories.location_settings import (
    LocationSettingsRepository,
    LocationSettingsRepositoryProtocol,
)
from .repositories.mining_actions import MiningActionRepository, MiningActionRepositoryProtocol
from .repositories.monsters_location import (
    MonsterLocationRepository,
    MonsterLocationRepositoryProtocol,
)
from .repositories.resources import ResourceRepository, ResourceRepositoryProtocol
from .services.character_resource import CharacterResourceService, CharacterResourceServiceProtocol
from .services.experience_for_level import (
    ExperienceForLevelService,
    ExperienceForLevelServiceProtocol,
)
from .services.location_resources import LocationResourceService, LocationResourceServiceProtocol
from .services.location_resources_character import (
    LocationResourcesCharacterService,
    LocationResourcesCharacterServiceProtocol,
)
from .services.location_settings import LocationSettingsService, LocationSettingsServiceProtocol
from .services.mining_templates import MiningTemplateService, MiningTemplateServiceProtocol
from .services.monster_location import MonsterLocationService, MonsterLocationServiceProtocol
from .services.resources import ResourceService, ResourceServiceProtocol

if TYPE_CHECKING:
    from .services.mining_actions import (
        CreateMiningActionServiceProtocol,
        MiningActionServiceProtocol,
        ProcessMiningActionServiceProtocol,
        ValidateCreateMiningActionServiceProtocol,
    )

from .events.handlers.mining import MiningEventHandler, MiningEventHandlerProtocol
from .events.handlers.subscriber import RedisSubscriber, RedisSubscriberProtocol
from .events.mining import MiningEvents, MiningEventsProtocol
from .events.monster import MonsterEvents, MonsterEventsProtocol
from .events.publisher import RedisPublisher, RedisPublisherProtocol
from .services.mining_actions import (
    CancelMiningProcessService,
    CreateMiningActionService,
    MiningActionService,
    ProcessMiningActionService,
    ValidateCreateMiningActionService,
)
from .use_cases.get_resources import (
    GetResourcesForCharacterUseCase,
    GetResourcesForCharacterUseCaseProtocol,
)
from .use_cases.initializators.init_experience_for_level import (
    InitializeExperiencesForLevelUseCase,
    InitializeExperiencesForLevelUseCaseProtocol,
)
from .use_cases.initializators.init_location_resources import (
    InitializeLocationResourcesUseCase,
    InitializeLocationResourcesUseCaseProtocol,
)
from .use_cases.initializators.init_location_settings import (
    InitializeLocationSettingsUseCase,
    InitializeLocationSettingsUseCaseProtocol,
)
from .use_cases.initializators.init_monsters_location import (
    InitializeMonsterLocationUseCase,
    InitializeMonsterLocationUseCaseProtocol,
)
from .use_cases.initializators.init_resources import (
    InitializeResourcesUseCase,
    InitializeResourcesUseCaseProtocol,
)
from .use_cases.mining.create import CreateMiningActionUseCase, CreateMiningActionUseCaseProtocol
from .use_cases.mining.get import GetMiningActionUseCase, GetMiningActionUseCaseProtocol
from .use_cases.mining.get_status import GetMiningStatusUseCase, GetMiningStatusUseCaseProtocol
from .use_cases.resources.get_by_slug import GetBySlugUseCase, GetBySlugUseCaseProtocol
from .use_cases.resources.get_my_resources import GetMyUseCase, GetMyUseCaseProtocol

_text_template_service: TextTemplateServiceProtocol = None

def get_text_template_service() -> TextTemplateServiceProtocol:
    return _text_template_service

def init_text_template_service(file_path: str):
    global _text_template_service
    _text_template_service = TextTemplateService(file_path)

def get_mining_template_service(template_service: TextTemplateServiceProtocol = Depends(get_text_template_service)) -> MiningTemplateServiceProtocol:
    return MiningTemplateService(template_service)

def get_redis_subscriber(redis_client: redis.Redis = Depends(get_redis_client)) -> RedisSubscriberProtocol:
    return RedisSubscriber(redis_client)

def __get_resource_repository(
    session: AsyncSession = Depends(get_async_session)
) -> ResourceRepositoryProtocol:
    return ResourceRepository(session=session)

def __get_location_resource_repository(
    session: AsyncSession = Depends(get_async_session)
) -> LocationResourceRepositoryProtocol:
    return LocationResourceRepository(session=session)

def get_resource_service(
    repository: ResourceRepositoryProtocol = Depends(__get_resource_repository)
) -> ResourceServiceProtocol:
    return ResourceService(repository=repository)

def get_initialize_resources(session: AsyncSession = Depends(get_async_session)) -> InitializeResourcesUseCaseProtocol:
    resource_repo = __get_resource_repository(session)
    resource_service = get_resource_service(resource_repo)
    return InitializeResourcesUseCase(resource_service)

def get_location_resource_service(
    repository: LocationResourceRepositoryProtocol = Depends(__get_location_resource_repository)
) -> LocationResourceServiceProtocol:
    return LocationResourceService(repository=repository)

def get_initialize_location_resources_use_case(
        session: AsyncSession = Depends(get_async_session)
    ) -> InitializeLocationResourcesUseCaseProtocol:
    location_resource_repository = __get_location_resource_repository(session=session)
    location_resource_service = get_location_resource_service(repository=location_resource_repository)
    return InitializeLocationResourcesUseCase(service=location_resource_service)

def __get_location_resources_character_repository(
    session: AsyncSession = Depends(get_async_session)
) -> LocationResourcesCharacterRepositoryProtocol:
    return LocationResourcesCharacterRepository(session=session)

def __get_character_location_level_repository(
    session: AsyncSession = Depends(get_async_session)
) -> CharacterLocationStatsRepositoryProtocol:
    return CharacterLocationStatsRepository(session=session)

def get_character_service_client(
    settings: Settings = Depends(get_settings)
) -> CharacterServiceClientProtocol:
    return CharacterServiceClient(
        base_url=settings.character_service_app.base_url
    )

def get_location_resources_character_service(
    repository: LocationResourcesCharacterRepositoryProtocol = Depends(__get_location_resources_character_repository),
    character_service_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    location_character_expierence_repository: CharacterLocationStatsRepositoryProtocol = Depends(__get_character_location_level_repository)
) -> LocationResourcesCharacterServiceProtocol:
    return LocationResourcesCharacterService(
        repository=repository,
        character_service_client=character_service_client,
        location_character_expierence_repository=location_character_expierence_repository
    )

def get_get_resources_for_character_use_case(
    service: LocationResourcesCharacterServiceProtocol = Depends(get_location_resources_character_service)
) -> GetResourcesForCharacterUseCaseProtocol:
    return GetResourcesForCharacterUseCase(service=service)

def get_get_my_resources_use_case(
    service: LocationResourcesCharacterServiceProtocol = Depends(get_location_resources_character_service)
) -> GetMyUseCaseProtocol:
    return GetMyUseCase(service)

def get_get_resource_by_slug_use_case(
        service: ResourceServiceProtocol = Depends(get_resource_service)
) -> GetBySlugUseCaseProtocol:
    return GetBySlugUseCase(service)

# monsters
def __get_monsters_repository(session: AsyncSession = Depends(get_async_session)) -> MonsterLocationRepositoryProtocol:
    return MonsterLocationRepository(session)

def get_monsters_service(repository: MonsterLocationRepositoryProtocol = Depends(__get_monsters_repository)) -> MonsterLocationServiceProtocol:
    return MonsterLocationService(repository)

def get_initialize_monsters_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeMonsterLocationUseCaseProtocol:
    repo = __get_monsters_repository(session)
    service = get_monsters_service(repo)
    return InitializeMonsterLocationUseCase(service)

# events
def get_redis_publisher(redis: redis.Redis = Depends(get_redis_client)) -> RedisPublisherProtocol:
    return RedisPublisher(redis)

def get_mining_events(publisher: RedisPublisher = Depends(get_redis_publisher)) -> MiningEventsProtocol:
    return MiningEvents(publisher)

def get_monster_events(publisher: RedisPublisher = Depends(get_redis_publisher)) -> MonsterEventsProtocol:
    return MonsterEvents(publisher)

# captcha client
def get_captcha_client(settings: Settings = Depends(get_settings)) -> CaptchaServiceClientProtocol:
    return CaptchaServiceClient(base_url=settings.captcha_service_app.base_url)

# character resource
def __get_character_resource_repository(
        session: AsyncSession = Depends(get_async_session)
) -> CharacterResourceRepositoryProtocol:
    return CharacterResourceRepository(session)

def get_character_resource_service(
        character_resource_repository: CharacterResourceRepositoryProtocol = Depends(__get_character_resource_repository)
) -> CharacterResourceServiceProtocol:
    return CharacterResourceService(character_resource_repository)

# experience for level
def __get_experience_for_level_repository(
    session: AsyncSession = Depends(get_async_session)
) -> ExperienceForLevelRepositoryProtocol:
    return ExperienceForLevelRepository(session=session)

def get_experience_for_level_service(
    repository: ExperienceForLevelRepositoryProtocol = Depends(__get_experience_for_level_repository)
) -> ExperienceForLevelServiceProtocol:
    return ExperienceForLevelService(repository=repository)

def get_initialize_experience_for_level_use_case(
        session: AsyncSession = Depends(get_async_session)
    ) -> InitializeExperiencesForLevelUseCaseProtocol:
    experience_for_level_repository = __get_experience_for_level_repository(session=session)
    experience_for_level_service = get_experience_for_level_service(repository=experience_for_level_repository)
    return InitializeExperiencesForLevelUseCase(service=experience_for_level_service)

# location settings
def __get_location_settings_repository(session: AsyncSession = Depends(get_async_session)) -> LocationSettingsRepositoryProtocol:
    return LocationSettingsRepository(session)

def get_location_settings_service(repository: LocationSettingsRepositoryProtocol = Depends(__get_location_settings_repository)) -> LocationSettingsServiceProtocol:
    return LocationSettingsService(repository)

def get_initialize_location_settings_use_case(session: AsyncSession = Depends(get_async_session)) -> InitializeLocationSettingsUseCaseProtocol:
    repo = __get_location_settings_repository(session)
    service = get_location_settings_service(repo)
    return InitializeLocationSettingsUseCase(service)

# mining actions
def __get_mining_action_repository(
    session: AsyncSession = Depends(get_async_session)
) -> MiningActionRepositoryProtocol:
    return MiningActionRepository(session=session)

def get_mining_action_service(
    repository: MiningActionRepositoryProtocol = Depends(__get_mining_action_repository)
) -> 'MiningActionServiceProtocol':
    return MiningActionService(repository=repository)

def get_get_mining_action_use_case(
    service: 'MiningActionServiceProtocol' = Depends(get_mining_action_service)
) -> GetMiningActionUseCaseProtocol:
    return GetMiningActionUseCase(service=service)

def get_create_mining_action_service(
    repository: MiningActionRepositoryProtocol = Depends(__get_mining_action_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    template_service: MiningTemplateServiceProtocol = Depends(get_mining_template_service),
    captcha_adapter: CaptchaServiceClientProtocol = Depends(get_captcha_client),
    settings: Settings = Depends(get_settings)
) -> 'CreateMiningActionServiceProtocol':
    return CreateMiningActionService(
        repository=repository,
        character_service=character_service,
        template_service=template_service,
        captcha_adapter=captcha_adapter,
        cooldown_seconds=settings.mining.cooldown_seconds,
        min_valid_level=settings.mining.min_valid_character_level,
        max_valid_tiredness=settings.mining.max_valid_character_tiredness
    )

def get_validate_mining_action_service(
        mining_checker: 'MiningActionServiceProtocol' = Depends(get_mining_action_service),
        mining_creator: 'CreateMiningActionServiceProtocol' = Depends(get_create_mining_action_service)
) -> 'ValidateCreateMiningActionServiceProtocol':
    return ValidateCreateMiningActionService(mining_checker=mining_checker,
                                             mining_creator=mining_creator)

def get_get_mining_status_use_case(
    service: 'MiningActionServiceProtocol' = Depends(get_mining_action_service)
) -> GetMiningStatusUseCaseProtocol:
    return GetMiningStatusUseCase(service=service)

def get_create_mining_action_use_case(
    service: 'ValidateCreateMiningActionServiceProtocol' = Depends(get_validate_mining_action_service)
) -> CreateMiningActionUseCaseProtocol:
    return CreateMiningActionUseCase(service=service)   

def get_cancel_mining_actions_factory():
    def factory(session: AsyncSession):
        repository = __get_mining_action_repository(session)
        return CancelMiningProcessService(repository)
    return factory

def get_mining_handler(
    redis_subscriber: RedisSubscriberProtocol = Depends(get_redis_subscriber),
    cancel_mining_service_factory: Callable[[AsyncSession], 'CancelMiningProcessService'] = Depends(get_cancel_mining_actions_factory)
) -> MiningEventHandlerProtocol:
    return MiningEventHandler(redis_subscriber, cancel_mining_service_factory)


# process mining action

def get_process_mining_action_service(
        mining_repository: MiningActionRepositoryProtocol = Depends(__get_mining_action_repository),
        experience_service: ExperienceForLevelServiceProtocol = Depends(get_experience_for_level_service),
        location_settings_service: LocationSettingsServiceProtocol = Depends(get_location_settings_service),
        location_resource_service: LocationResourceServiceProtocol = Depends(get_location_resource_service),
        location_resources_character_repository: LocationResourcesCharacterRepositoryProtocol = Depends(__get_location_resources_character_repository),
        location_character_experience_repository: CharacterLocationStatsRepositoryProtocol = Depends(__get_character_location_level_repository),
        character_resource_service: CharacterResourceServiceProtocol = Depends(get_character_resource_service),
        mining_event: MiningEventsProtocol = Depends(get_mining_events),
        monster_event: MonsterEventsProtocol = Depends(get_monster_events),
        character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
        monster_service: MonsterLocationServiceProtocol = Depends(get_monsters_service),
        template_service: MiningTemplateServiceProtocol = Depends(get_mining_template_service),
        redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
        settings: Settings = Depends(get_settings)
) -> 'ProcessMiningActionServiceProtocol':
    return ProcessMiningActionService(
        repository=mining_repository,
        experience_service=experience_service,
        location_settings_service=location_settings_service,
        location_resource_service=location_resource_service,
        location_resources_character_repository=location_resources_character_repository,
        location_character_experience_repository=location_character_experience_repository,
        character_resource_service=character_resource_service,
        mining_events=mining_event,
        monster_events=monster_event,
        character_service=character_service,
        monster_service=monster_service,
        template_service=template_service,
        redis_publisher=redis_publisher,
        change_tiredness=settings.mining.change_tiredness,
        min_attack_monster_health_percentage=settings.mining.min_attack_monster_health_percentage,
        min_attack_monster_tiredness=settings.mining.min_attack_monster_tiredness,
        default_monster_attack_chance=settings.mining.default_monster_attack_chance,
        default_attack_monster_standart=settings.mining.default_attack_monster_standart
    )


