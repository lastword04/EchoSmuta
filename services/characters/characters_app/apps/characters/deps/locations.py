from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ...stats.services.effective_stats import EffectiveStatsService
from ..events.change_location import ChangeLocationEvents, ChangeLocationEventsProtocol
from ..events.publisher import RedisPublisherProtocol
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..repositories.locations.locations import LocationRepositoryProtocol, LocationRepository
from ..repositories.locations.locations_stats import LocationsStatsRepositoryProtocol, LocationsStatsRepository
from ..services.locations.locations import LocationServiceProtocol, LocationService
from ..services.locations.locations_stats import LocationsStatsServiceProtocol, LocationsStatsService
from ..services.locations.character_location import CharacterLocationServiceProtocol, CharacterLocationService
from ..use_cases.locations.count_characters_by_locations import CountCharactersByLocationUseCaseProtocol, CountCharactersByLocationUseCase
from ..use_cases.locations.get_by_slug import GetLocationBySlugUseCaseProtocol, GetLocationBySlugUseCase
from ..use_cases.locations.change_location import ChangeCharacterLocationUseCaseProtocol, ChangeCharacterLocationUseCase
from ..use_cases.initializators.init_locations import InitializeLocationsUseCaseProtocol, InitializeLocationsUseCase
from ...rest.services.house_guest_service import HouseGuestServiceProtocol
from ...rest.services.rest_service import RestServiceProtocol
from ...rest.depends import get_house_guest_service, get_rest_service
from .adapters import get_redis_publisher, get_effective_stats_service
from .cities import __get_city_repository, get_city_service
from .valid import __get_character_repository


def __get_location_repository(session: AsyncSession = Depends(get_async_session)) -> LocationRepositoryProtocol:
    return LocationRepository(session=session)


def get_location_service(repository: LocationRepositoryProtocol = Depends(__get_location_repository)) -> LocationServiceProtocol:
    return LocationService(repository=repository)


def get_initialize_locations_use_case(session: AsyncSession) -> InitializeLocationsUseCaseProtocol:
    repo = __get_location_repository(session=session)
    city_repo = __get_city_repository(session=session)
    city_service = get_city_service(repository=city_repo)
    service = get_location_service(repository=repo)
    return InitializeLocationsUseCase(service=service, city_service=city_service)


def get_locations_stats_repository(session: AsyncSession = Depends(get_async_session)) -> LocationsStatsRepositoryProtocol:
    return LocationsStatsRepository(session=session)


def get_locations_stats_service(repository: LocationsStatsRepositoryProtocol = Depends(get_locations_stats_repository)) -> LocationsStatsServiceProtocol:
    return LocationsStatsService(repository=repository)


def get_count_characters_by_location_use_case(service: LocationsStatsServiceProtocol = Depends(get_locations_stats_service)) -> CountCharactersByLocationUseCaseProtocol:
    return CountCharactersByLocationUseCase(service=service)


def get_location_by_slug_use_case(service: LocationServiceProtocol = Depends(get_location_service)) -> GetLocationBySlugUseCaseProtocol:
    return GetLocationBySlugUseCase(service=service)


def get_change_location_event(publisher: RedisPublisherProtocol = Depends(get_redis_publisher)) -> ChangeLocationEventsProtocol:
    return ChangeLocationEvents(publisher)


def get_character_location_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
                                   location_repository: LocationRepositoryProtocol = Depends(__get_location_repository),
                                   change_location_event: ChangeLocationEventsProtocol = Depends(get_change_location_event)) -> CharacterLocationServiceProtocol:
    return CharacterLocationService(location_repository=location_repository,
                                    character_repository=repository,
                                    character_location_event=change_location_event)


def get_change_character_location_use_case(
    service: CharacterLocationServiceProtocol = Depends(get_character_location_service),
    effective_stats: EffectiveStatsService = Depends(get_effective_stats_service),
    house_guest_service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
    rest_service: RestServiceProtocol = Depends(get_rest_service),
    character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> ChangeCharacterLocationUseCaseProtocol:
    return ChangeCharacterLocationUseCase(
        service=service,
        effective_stats=effective_stats,
        house_guest_service=house_guest_service,
        rest_service=rest_service,
        character_repository=character_repository,
    )
