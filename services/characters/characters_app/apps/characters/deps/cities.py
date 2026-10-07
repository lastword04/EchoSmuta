from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.cities.cities import CityRepositoryProtocol, CityRepository
from ..services.cities.cities import CityServiceProtocol, CityService
from ..use_cases.initializators.init_cities import InitializeCitiesUseCaseProtocol, InitializeCitiesUseCase


def __get_city_repository(session: AsyncSession = Depends(get_async_session)) -> CityRepositoryProtocol:
    return CityRepository(session=session)


def get_city_service(repository: CityRepositoryProtocol = Depends(__get_city_repository)) -> CityServiceProtocol:
    return CityService(repository=repository)


def get_initialize_cities_use_case(session: AsyncSession) -> InitializeCitiesUseCaseProtocol:
    repo = __get_city_repository(session=session)
    service = get_city_service(repository=repo)
    return InitializeCitiesUseCase(service=service)
