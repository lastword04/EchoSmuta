from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...adapters.characters import CharacterServiceClientProtocol
from ...schemas import CharacterCityTradeStatsReadSchema
from ...services.stats.character_city_trade_stats import (
    CharacterCityTradeStatsServiceProtocol,
)

# ✅ НОВОЕ: воркшоп -> родительская локация
WORKSHOP_TO_PARENT_MAP = {
    '1.35.laboratory': '1.9.pharmacy',
    '1.36.kitchen': '1.25.fish-shop',
    '1.37.carpentry-workshop': '1.21.furniture-shop',
    '1.38.hunter-workshop': '1.22.hunting-shop',
    '1.39.incubator': '1.24.bird-market',
}


class GetCharacterCityTradeStatsUseCaseProtocol(UseCaseProtocol[CharacterCityTradeStatsReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, location_slug: str | None = None) -> CharacterCityTradeStatsReadSchema:
        ...


class GetCharacterCityTradeStatsUseCase(GetCharacterCityTradeStatsUseCaseProtocol):
    def __init__(
        self: Self,
        service: CharacterCityTradeStatsServiceProtocol,
        character_client: CharacterServiceClientProtocol
    ):
        self.service = service
        self.character_client = character_client

    async def __call__(self: Self, token: UserTokenDataReadSchema, location_slug: str | None = None) -> CharacterCityTradeStatsReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()

        # ОПТИМИЗАЦИЯ: используем location_slug с фронта, если он есть,
        # и НЕ делаем синхронный HTTP-запрос к characters-сервису
        if location_slug:
            target_slug = location_slug
        else:
            # Fallback: запрашиваем баланс/локацию через HTTP только если фронт не передал
            character = await self.character_client.get_simple_character_balance(token.character_id)
            target_slug = character.location_slug

        # Если персонаж в воркшопе — берём статистику родительской локации
        stats_slug = WORKSHOP_TO_PARENT_MAP.get(target_slug, target_slug)

        stats = await self.service.get_or_create(token.character_id, stats_slug)

        return stats