import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol

from shared.schemas.base import StatusOkSchema
from shared.schemas.files import FileReadSchema
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from .....core.utils.exceptions import ModelFieldNotFoundException
from ....resources.events.publisher import RedisPublisherProtocol
from ...adapters.characters import CharacterServiceClientProtocol
from ...adapters.file_storage import FileServiceClientProtocol
from ...events.items import ItemEventsProtocol
from ...exceptions import (
    InsufficientCharacterDucatsForCityTradeShopError,
    InsufficientCharacterLevelForCityTradeShopError,
)
from ...models import CityTradingShop
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...repositories.sale.sale_inventory_items import (
    SaleInventoryItemRepositoryProtocol,
)
from ...repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ...repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ...schemas import (
    CityTradingShopCreateSchema,
    CityTradingShopReadSchema,
    CityTradingShopResponseSchema,
    CityTradingShopSettingsReadSchema,
    CityTradingShopUpdateInfoSchema,
    CityTradingShopUpdatePhotoSchema,
    CityTradingShopWithSaleItemsSchema,
    ShopSaleItemSchema,
)
from ...services.adapters.item_templates import ItemTemplateServiceProtocol
from ...services.stats.character_city_trade_stats import (
    CharacterCityTradeStatsServiceProtocol,
)

logger = logging.getLogger(__name__)

class CityTradingShopCharacterServiceProtocol(Protocol):
    async def get_for_character(self, character_id: uuid.UUID, location_slug: str | None = None) -> CityTradingShopResponseSchema:
        ...

    async def create_for_character(self, character_id: uuid.UUID) -> CityTradingShopResponseSchema:
        ...

    async def get(self, id: uuid.UUID) -> CityTradingShopResponseSchema:
        ...

    async def get_by_number(self, character_id: uuid.UUID, number: int) -> CityTradingShopResponseSchema:
        ...

    async def get_shops_with_sale_items_paginated(
        self, location_slug: str, page: int, page_size: int,
        item_name: str | None = None,
        number: int | None = None,
        minimal_level: int | None = None,
        item_kind: str | None = None,
    ) -> tuple[list, int]:
        ...

class CityTradingShopCharacterService(CityTradingShopCharacterServiceProtocol):
    def __init__(self, repository: CityTradingShopCharacterRepositoryProtocol,
                 city_settings_repo: CityTradingShopSettingsRepositoryProtocol,
                 city_settings_buy_repo: CityTradingShopBuySettingsRepositoryProtocol,
                 character_service: CharacterServiceClientProtocol,
                 file_service: FileServiceClientProtocol,
                 sale_repository: SaleInventoryItemRepositoryProtocol,
                 city_trade_stats_service: CharacterCityTradeStatsServiceProtocol,
                 template_service: ItemTemplateServiceProtocol,
                 items_events: ItemEventsProtocol):
        self.repository = repository
        self.city_settings_repo = city_settings_repo
        self.city_settings_buy_repo = city_settings_buy_repo
        self.character_service = character_service
        self.file_service = file_service
        self.sale_repository = sale_repository
        self.city_trade_stats_service = city_trade_stats_service
        self.template_service = template_service
        self.items_events = items_events

    async def get_for_character(self, character_id: uuid.UUID, location_slug: str | None = None) -> CityTradingShopResponseSchema:
        character = await self.character_service.get_simple_character_balance(character_id)
        
        # Используем location_slug из параметра, если передан, иначе из БД
        target_location_slug = location_slug or character.location_slug
        
        city_trading_shop = await self.repository.get_for_character(character.id, target_location_slug)

        settings, photo = await self._get_settings_and_photo_for_city_shop(city_trading_shop)
        sale_items_raw = await self.sale_repository.get_sale_items_by_shop(city_trading_shop.id)
        
        # Конвертируем SaleInventoryItemReadSchema в ShopSaleItemSchema
        sale_items = [
            ShopSaleItemSchema(
                sale_id=item.id,
                inventory_item_id=item.inventory_item_id,
                price=item.price,
                item_slug=item.item_slug,
                amount=item.amount,
                expired_date=item.expired_date,
                used_count=item.used_count,
                wear=item.wear,
                item_name=item.item_name,
                ability_parameters=item.ability_parameters,
                parameters=item.parameters,          
                item_type=item.item_type,           
                minimal_level=item.minimal_level    
            )
            for item in sale_items_raw
        ]

        return CityTradingShopResponseSchema(
            shop=city_trading_shop,
            settings=settings,
            photo=photo,
            sale_items=sale_items
        )
    
    
    async def get(self, id: uuid.UUID) -> CityTradingShopResponseSchema:
        city_trading_shop = await self.repository.get(id)

        settings, photo = await self._get_settings_and_photo_for_city_shop(city_trading_shop)
        sale_items_raw = await self.sale_repository.get_sale_items_by_shop(city_trading_shop.id)
        
        # Конвертируем SaleInventoryItemReadSchema в ShopSaleItemSchema
        sale_items = [
            ShopSaleItemSchema(
                sale_id=item.id,
                inventory_item_id=item.inventory_item_id,
                price=item.price,
                item_slug=item.item_slug,
                amount=item.amount,
                expired_date=item.expired_date,
                used_count=item.used_count,
                wear=item.wear,
                item_name=item.item_name,
                ability_parameters=item.ability_parameters,
                parameters=item.parameters,         
                item_type=item.item_type,           
                minimal_level=item.minimal_level   
            )
            for item in sale_items_raw
        ]

        return CityTradingShopResponseSchema(
            shop=city_trading_shop,
            settings=settings,
            photo=photo,
            sale_items=sale_items
        )
    

    async def get_by_number(self, character_id: uuid.UUID, number: int) -> CityTradingShopResponseSchema:
        character = await self.character_service.get_simple_character_balance(character_id)
        
        city_trading_shop = await self.repository.get_by_number(character.location_slug, number)

        settings, photo = await self._get_settings_and_photo_for_city_shop(city_trading_shop)
        sale_items_raw = await self.sale_repository.get_sale_items_by_shop(city_trading_shop.id)
        
        # Конвертируем SaleInventoryItemReadSchema в ShopSaleItemSchema
        sale_items = [
            ShopSaleItemSchema(
                sale_id=item.id,
                inventory_item_id=item.inventory_item_id,
                price=item.price,
                item_slug=item.item_slug,
                amount=item.amount,
                expired_date=item.expired_date,
                used_count=item.used_count,
                wear=item.wear,
                item_name=item.item_name,
                ability_parameters=item.ability_parameters,
                parameters=item.parameters,         
                item_type=item.item_type,            
                minimal_level=item.minimal_level     
            )
            for item in sale_items_raw
        ]

        return CityTradingShopResponseSchema(
            shop=city_trading_shop,
            settings=settings,
            photo=photo,
            sale_items=sale_items
        )        
    

    async def get_shops_with_sale_items_paginated(
        self, location_slug: str, page: int, page_size: int,
        item_name: str | None = None,   
        number: int | None = None,   
        minimal_level: int | None = None,
        item_kind: str | None = None,   
    ) -> tuple[list[CityTradingShopWithSaleItemsSchema], int]:
        shops, total = await self.repository.get_shops_with_sale_items_paginated(
            location_slug, page, page_size,
            item_name=item_name,  
            number=number,       
            minimal_level=minimal_level,
            item_kind=item_kind, 
        )
        
        # Собираем все photo_id для пачковой загрузки
        photo_ids = [shop['photo_id'] for shop in shops if shop.get('photo_id') is not None]
        
        # Загружаем все фотки одним запросом
        photos_dict = {}
        if photo_ids:
            photos_response = await self.file_service.get_by_ids(photo_ids)
            photos_dict = {photo.id: photo for photo in photos_response.files}
        
        # Добавляем фотки к магазинам
        shops_with_photos = []
        for shop in shops:
            photo = photos_dict.get(shop['photo_id']) if shop.get('photo_id') else None
            shop['photo'] = photo
            shops_with_photos.append(CityTradingShopWithSaleItemsSchema(**shop))
        
        return shops_with_photos, total


    async def create_for_character(self, character_id: uuid.UUID) -> CityTradingShopResponseSchema:
        character = await self.character_service.get_simple_character_balance(character_id)
        buy_settings = await self.city_settings_buy_repo.get_by_location_slug(character.location_slug)

        if character.level < buy_settings.min_level:
            raise InsufficientCharacterLevelForCityTradeShopError(
                required_level=buy_settings.min_level,
                current_level=character.level,                
            )
        new_ducats = character.ducats - buy_settings.price
        if new_ducats < 0:
            raise InsufficientCharacterDucatsForCityTradeShopError(
                required_ducats=buy_settings.price,
                current_ducats=character.ducats,                
            )

        name = self._get_standart_name_city_shop(character.location_slug)
        city_trade_for_create = CityTradingShopCreateSchema(
            location_slug=character.location_slug,
            character_id=character.id,
            character_name=character.name,
            name=name,
        )
        created_city_trade = await self.repository.create(city_trade_for_create)
        
        # Create stats record for character city trade
        await self.city_trade_stats_service.get_or_create(character.id, character.location_slug)
        
        # Проводим списание через ledger с метаданными
        await self.character_service.debit_ducats(
            character.id,
            buy_settings.price,
            operation_type="tent_purchase",
            source="mining.trade_tent",
            item_meta={"location_slug": created_city_trade.location_slug, "shop_number": created_city_trade.number}
        )
        settings = await self.city_settings_repo.get_by_location_and_level(
            created_city_trade.location_slug,
            created_city_trade.level
        )
        city_name = self.template_service.get_city_name(created_city_trade.location_slug)
        private_message = self.template_service.get_shop_purchase_message(
            location_slug=created_city_trade.location_slug,
            number=created_city_trade.number,
            city_name=city_name,
        )
        public_message = self.template_service.get_shop_purchase_public_message(
            location_slug=created_city_trade.location_slug,
            character_name=character.name,
            number=created_city_trade.number,
            city_name=city_name,
        )

        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="shop_purchase_private",
                character_id=character.id,
                location_slug=created_city_trade.location_slug,
                content=private_message,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[character.id],
            )
        )
        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="shop_purchase_city",
                character_id=character.id,
                location_slug=created_city_trade.location_slug,
                content=public_message,
                scope=ItemMessageScope.CITY,
            )
        )

        return CityTradingShopResponseSchema(
            shop=created_city_trade,
            settings=settings,
            photo=None,
        )
    
    
    async def _get_settings_and_photo_for_city_shop(self, city_trading_shop: CityTradingShopReadSchema) -> tuple[CityTradingShopSettingsReadSchema, FileReadSchema | None]:
        settings, photo = None, None
        settings_task = self.city_settings_repo.get_by_location_and_level(
            city_trading_shop.location_slug,
            city_trading_shop.level
        )
    
        # Условно создаём задачу для фото
        photo_task = (
            self.file_service.get(city_trading_shop.photo_id)
            if city_trading_shop.photo_id
            else None
        )
        
        # Выполняем параллельно, если есть фото
        if photo_task:
            settings, photo = await asyncio.gather(
                settings_task, 
                photo_task,
                return_exceptions=True
            )
            
            # Обработка ошибки фото (пример)
            if isinstance(photo, Exception):
                logger.warning(f"Photo load failed: {photo}")
                photo = None
        else:
            settings = await settings_task
            photo = None

        return settings, photo 
    

    def _get_standart_name_city_shop(self, location_slug: str) -> str:
        STANDART_NAMES = {
            "1.9.pharmacy": "Аптека",
            "1.13.forge": "Кузница",
            "1.21.furniture-shop": "Мебельная лавка",
            "1.22.hunting-shop": "Охотничья лавка",
            "1.24.bird-market": "Питомник",
            "1.25.fish-shop": "Рыбная лавка",
            "1.27.trade-hall": "Палатка",
        }
        result = STANDART_NAMES.get(location_slug)

        if result is None:
            raise ModelFieldNotFoundException(CityTradingShop, "location_slug", location_slug)
        
        return result
    

class UpdateCityTradingShopServiceProtocol(Protocol):
    async def update_license_duration(
        self,
        id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> CityTradingShopReadSchema:
        ...


    async def update_info(self,  id: uuid.UUID, update_schema: CityTradingShopUpdateInfoSchema, character_id: uuid.UUID) -> CityTradingShopReadSchema:
        ...


    async def update_photo(self, id: uuid.UUID, photo_schema: CityTradingShopUpdatePhotoSchema, character_id: uuid.UUID) -> StatusOkSchema:
        ...

    async def level_up_shop(self, character_id: uuid.UUID) -> CityTradingShopResponseSchema:
        ...


class UpdateCityTradingShopService(UpdateCityTradingShopServiceProtocol):
    def __init__(self, repository: CityTradingShopCharacterRepositoryProtocol,
                 city_settings_repo: CityTradingShopSettingsRepositoryProtocol,
                 character_service: CharacterServiceClientProtocol,
                 template_service: ItemTemplateServiceProtocol,
                 items_events: ItemEventsProtocol,
                 redis_publisher: RedisPublisherProtocol,
                 license_renewal_cost: int = 15,
                 license_renewal_days: int = 14):
        self.repository = repository
        self.city_settings_repo = city_settings_repo
        self.character_service = character_service
        self.template_service = template_service
        self.items_events = items_events
        self.redis_publisher = redis_publisher
        self.license_renewal_cost = license_renewal_cost
        self.license_renewal_days = license_renewal_days


    async def update_license_duration(
        self,
        id: uuid.UUID,
        character_id: uuid.UUID
    ) -> CityTradingShopReadSchema:
        character = await self.character_service.get_simple_character_balance(character_id)
        new_ducats = character.ducats - self.license_renewal_cost
        if new_ducats <  0:
            raise InsufficientCharacterDucatsForCityTradeShopError(
                required_ducats=self.license_renewal_cost,
                current_ducats=character.ducats,                
            )
        
        duration = timedelta(days=self.license_renewal_days)
        result = await self.repository.update_license_duration(id, character_id, duration)
        
        await self.character_service.debit_ducats(
            character.id,
            self.license_renewal_cost,
            operation_type="tent_license_renewal",
            source="mining.trade_tent",
            item_meta={"shop_id": str(id)}
        )
        
        end_license = result.end_license or datetime.now(UTC)
        system_message = self.template_service.get_license_renewal_message(
            location_slug=result.location_slug,
            end_license=end_license.strftime("%d.%m.%Y %H:%M"),
        )
        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="shop_license_renewal",
                character_id=character_id,
                location_slug=result.location_slug,
                content=system_message,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[character_id],
            )
        )

        return result


    async def update_info(self, id: uuid.UUID, update_schema: CityTradingShopUpdateInfoSchema, character_id: uuid.UUID) -> CityTradingShopReadSchema:
        result = await self.repository.update_info(id, update_schema, character_id)

        try:
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "shop_info_updated",
                    "shop_id": str(result.id),
                    "location_slug": result.location_slug,
                    "initiator_character_id": str(character_id),
                    "partner_character_id": None,
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish shop_info_updated: %s", e)

        return result

    
    async def update_photo(self, id: uuid.UUID, photo_schema: CityTradingShopUpdatePhotoSchema, character_id: uuid.UUID) -> StatusOkSchema:
        result = await self.repository.update_photo(id, photo_schema, character_id)

        try:
            shop = await self.repository.get(id)
            payload = {
                "event_type": "economy_state_updated",
                "data": {
                    "action": "shop_photo_updated",
                    "shop_id": str(id),
                    "location_slug": shop.location_slug,
                    "initiator_character_id": str(character_id),
                    "partner_character_id": None,
                }
            }
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception as e:
            logger.warning("Failed to publish shop_photo_updated: %s", e)

        return result


    async def level_up_shop(self, character_id: uuid.UUID) -> CityTradingShopResponseSchema:
        """
        Повышает уровень магазина на 1.
        Проверяет достаточность дукатов, списывает их, обновляет уровень магазина,
        загружает новые настройки для нового уровня и возвращает обновленный магазин.
        """
        # Получаем персонажа и его магазин
        character = await self.character_service.get_simple_character_balance(character_id)
        shop = await self.repository.get_for_character(character_id, character.location_slug)
        
        # Получаем текущие настройки магазина
        current_settings = await self.city_settings_repo.get_by_location_and_level(
            shop.location_slug,
            shop.level
        )
        
        # Проверяем что есть цена для повышения уровня
        if current_settings.price_up_level is None:
            from ...exceptions import NotEnoughDucatsError
            raise NotEnoughDucatsError(
                required_ducats=0,
                current_ducats=0,
            )
        
        # Проверяем достаточность дукатов
        new_ducats = character.ducats - current_settings.price_up_level
        if new_ducats < 0:
            raise InsufficientCharacterDucatsForCityTradeShopError(
                required_ducats=current_settings.price_up_level,
                current_ducats=character.ducats,                
            )
        
        # Обновляем дукаты персонажа через ledger
        await self.character_service.debit_ducats(
            character.id,
            current_settings.price_up_level,
            operation_type="tent_upgrade",
            source="mining.trade_tent",
            item_meta={"location_slug": shop.location_slug, "current_level": shop.level}
        )
        
        # Повышаем уровень магазина
        updated_shop = await self.repository.update_shop_level(shop.id, character_id)
        
        # Загружаем новые настройки для нового уровня
        new_settings = await self.city_settings_repo.get_by_location_and_level(
            updated_shop.location_slug,
            updated_shop.level
        )
        
        system_message = self.template_service.get_level_up_message(
            location_slug=updated_shop.location_slug,
            level=updated_shop.level,
        )
        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="shop_level_up",
                character_id=character_id,
                location_slug=updated_shop.location_slug,
                content=system_message,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[character_id],
            )
        )

        return CityTradingShopResponseSchema(
            shop=updated_shop,
            settings=new_settings,
            photo=None,
        )
