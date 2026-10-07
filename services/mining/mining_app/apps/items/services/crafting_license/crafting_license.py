import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from fastapi import status

from shared.exceptions import CoreException
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from ...adapters.characters import CharacterServiceClientProtocol
from ...events.items import ItemEventsProtocol
from ...exceptions import InsufficientCharacterLevelForCityTradeShopError
from ...repositories.crafting_license.crafting_license import (
    CraftingLicenseRepositoryProtocol,
)
from ...repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ...schemas import CraftingLicenseReadSchema
from ...services.adapters.item_templates import ItemTemplateServiceProtocol

logger = logging.getLogger(__name__)

LICENSE_DURATION_DAYS = 14
BUY_PRICE = Decimal(500)
RENEW_PRICE = Decimal(15)

class NoCraftingLicenseError(CoreException):
    def __init__(self, location_slug: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No active crafting license for {location_slug}",
            error_code="NO_CRAFTING_LICENSE"
        )

class CraftingLicenseServiceProtocol(Protocol):
    async def get_status(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema: ...
    async def buy_license(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema: ...
    async def renew_license(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema: ...

class CraftingLicenseService:
    def __init__(
        self,
        repo: CraftingLicenseRepositoryProtocol,
        character_client: CharacterServiceClientProtocol,
        template_service: ItemTemplateServiceProtocol,
        items_events: ItemEventsProtocol,
        city_settings_buy_repo: CityTradingShopBuySettingsRepositoryProtocol,
    ):
        self.repo = repo
        self.character_client = character_client
        self.template_service = template_service
        self.items_events = items_events
        self.city_settings_buy_repo = city_settings_buy_repo

    async def get_status(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema:
        lic = await self.repo.get_for_character(character_id, location_slug)
        now = datetime.now(UTC)
        is_active = lic is not None and lic.end_date > now
        return CraftingLicenseReadSchema(
            id=lic.id if lic else None,
            character_id=character_id,
            location_slug=location_slug,
            end_date=lic.end_date if lic else None,
            is_active=is_active,
            number=lic.number if lic else None
        )

    async def buy_license(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema:
        license_status = await self.get_status(character_id, location_slug)
        if license_status.is_active:
            raise CoreException(status.HTTP_400_BAD_REQUEST, "License already active")

        character = await self.character_client.get_simple_character_balance(character_id)
        
        # 🛡️ Проверка уровня
        buy_settings = await self.city_settings_buy_repo.get_by_location_slug(location_slug)
        if buy_settings and character.level < buy_settings.min_level:
            raise InsufficientCharacterLevelForCityTradeShopError(
                required_level=buy_settings.min_level,
                current_level=character.level,
            )
        
        if character.ducats < BUY_PRICE:
            from ...exceptions import InsufficientCharacterDucatsForCityTradeShopError
            raise InsufficientCharacterDucatsForCityTradeShopError(
                required_ducats=BUY_PRICE,
                current_ducats=character.ducats,
            )

        # Используем ledger-aware debit с метаданными
        await self.character_client.debit_ducats(
            character_id,
            BUY_PRICE,
            operation_type="crafting_license_purchase",
            source=f"mining.{location_slug}",
            item_meta={"location_slug": location_slug}
        )
        # Получаем следующий номер для этой локации
        number = await self.repo.get_next_number(location_slug)

        end_date = datetime.now(UTC) + timedelta(days=LICENSE_DURATION_DAYS)
        lic = await self.repo.create({
            "character_id": character_id,
            "location_slug": location_slug,
            "end_date": end_date,
            "number": number
        })

        # ✅ НОВОЕ: сообщения обёрнуты в try/except — покупка не должна падать
        try:
            # Сообщение о покупке (себе)
            city_name = self.template_service.get_city_name(location_slug)
            msg_self = self.template_service.get_shop_purchase_message(location_slug, number, city_name)
            await self.items_events.publish_message(ItemMessageEventSchema(
                event_type="license_purchase",
                character_id=character_id,
                location_slug=location_slug,
                content=msg_self,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[character_id],
            ))

            # Публичное сообщение (для других игроков)
            character_name = character.name
            msg_public = self.template_service.get_shop_purchase_public_message(
                location_slug, character_name, number, city_name
            )
            await self.items_events.publish_message(ItemMessageEventSchema(
                event_type="license_purchase_public",
                character_id=character_id,
                location_slug=location_slug,
                content=msg_public,
                scope=ItemMessageScope.CITY,
                target_user_ids=None,
            ))
        except Exception as e:
            logger.warning("Failed to send license purchase messages for %s: %s", location_slug, e)

        return CraftingLicenseReadSchema(
            id=lic.id, character_id=lic.character_id,
            location_slug=lic.location_slug, end_date=lic.end_date, is_active=True,
            number=lic.number
        )

    async def renew_license(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema:
        lic = await self.repo.get_for_character(character_id, location_slug)
        if not lic:
            raise CoreException(status.HTTP_404_NOT_FOUND, "License not found, buy it first")

        character = await self.character_client.get_simple_character_balance(character_id)
        if character.ducats < RENEW_PRICE:
            from ...exceptions import InsufficientCharacterDucatsForCityTradeShopError
            raise InsufficientCharacterDucatsForCityTradeShopError(
                required_ducats=RENEW_PRICE,
                current_ducats=character.ducats,
            )

        await self.character_client.debit_ducats(
            character_id,
            RENEW_PRICE,
            operation_type="crafting_license_renewal",
            source=f"mining.{location_slug}",
            item_meta={"location_slug": location_slug}
        )
        new_end = max(lic.end_date, datetime.now(UTC)) + timedelta(days=LICENSE_DURATION_DAYS)
        lic = await self.repo.update(lic, new_end)

        # ✅ НОВОЕ: сообщение обёрнуто в try/except — продление не должно падать
        try:
            end_date_str = lic.end_date.strftime("%d.%m.%Y %H:%M")
            msg = self.template_service.get_license_renewal_message(location_slug, end_date_str)
            await self.items_events.publish_message(ItemMessageEventSchema(
                event_type="license_renewal",
                character_id=character_id,
                location_slug=location_slug,
                content=msg,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[character_id],
            ))
        except Exception as e:
            logger.warning("Failed to send license renewal message for %s: %s", location_slug, e)

        return CraftingLicenseReadSchema(
            id=lic.id, character_id=lic.character_id,
            location_slug=lic.location_slug, end_date=lic.end_date, is_active=True,
            number=lic.number
        )