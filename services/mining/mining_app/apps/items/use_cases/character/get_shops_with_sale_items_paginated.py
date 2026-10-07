from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema

from ...adapters.characters import CharacterServiceClientProtocol
from ...schemas import PaginatedShopsWithSaleItemsSchema
from ...services.city_trading_character.city_trading import (
    CityTradingShopCharacterServiceProtocol,
)


class GetShopsWithSaleItemsPaginatedUseCaseProtocol(Protocol):
    async def __call__(
        self, 
        page: int, 
        page_size: int, 
        user: UserTokenDataReadSchema,
        item_name: str | None = None,  
        number: int | None = None,
        minimal_level: int | None = None,
        item_kind: str | None = None,
        location_slug: str | None = None,
    ) -> PaginatedShopsWithSaleItemsSchema:
        ...


class GetShopsWithSaleItemsPaginatedUseCase(GetShopsWithSaleItemsPaginatedUseCaseProtocol):
    def __init__(
        self, 
        service: CityTradingShopCharacterServiceProtocol,
        character_client: CharacterServiceClientProtocol
    ):
        self.service = service
        self.character_client = character_client

    async def __call__(
        self, 
        page: int, 
        page_size: int, 
        user: UserTokenDataReadSchema,
        item_name: str | None = None,  
        number: int | None = None,
        minimal_level: int | None = None,
        item_kind: str | None = None,
        location_slug: str | None = None,
    ) -> PaginatedShopsWithSaleItemsSchema:
        
        # ОПТИМИЗАЦИЯ: используем location_slug с фронта, если он есть,
        # и НЕ делаем синхронный HTTP-запрос к characters-сервису
        if location_slug:
            target_location = location_slug
        else:
            # Fallback: запрашиваем баланс/локацию через HTTP только если фронт не передал
            character = await self.character_client.get_simple_character_balance(user.character_id)
            target_location = character.location_slug
        
        shops, total = await self.service.get_shops_with_sale_items_paginated(
            target_location,
            page, 
            page_size,
            item_name=item_name,  
            number=number,
            minimal_level=minimal_level,
            item_kind=item_kind,
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedShopsWithSaleItemsSchema(
            items=shops,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )