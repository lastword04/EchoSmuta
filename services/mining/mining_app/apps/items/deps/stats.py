"""Провайдеры статистики торговли персонажа (stats-домен)."""
from fastapi import Depends

from ..adapters.characters import CharacterServiceClientProtocol
from ..repositories.stats.character_city_trade_stats import (
    CharacterCityTradeStatsRepositoryProtocol,
)
from ..services.stats.character_city_trade_stats import (
    CharacterCityTradeStatsService,
    CharacterCityTradeStatsServiceProtocol,
)
from ..use_cases.stats.get_character_city_trade_stats import (
    GetCharacterCityTradeStatsUseCase,
    GetCharacterCityTradeStatsUseCaseProtocol,
)
from .adapters import get_character_service_client
from .repositories import _get_character_city_trade_stats_repository


def get_character_city_trade_stats_service(repository: CharacterCityTradeStatsRepositoryProtocol = Depends(_get_character_city_trade_stats_repository)) -> CharacterCityTradeStatsServiceProtocol:
    return CharacterCityTradeStatsService(repository=repository)


def get_get_character_city_trade_stats_use_case(
    service: CharacterCityTradeStatsServiceProtocol = Depends(get_character_city_trade_stats_service),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)
) -> GetCharacterCityTradeStatsUseCaseProtocol:
    return GetCharacterCityTradeStatsUseCase(service=service, character_client=character_client)
