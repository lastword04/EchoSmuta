import logging
import uuid
import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from shared.schemas.base import StatusOkSchema
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from ....resources.events.publisher import RedisPublisherProtocol
from ...adapters.characters import CharacterServiceClientProtocol
from ...events.items import ItemEventsProtocol
from ...exceptions import (
    CharacterWeightExceededError,
    CityTradingShopLicenseExpiredError,
    InsufficientDucatsToBuyError,
    ItemNotForSaleError,
)
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...repositories.sale.sale_history import SaleHistoryRepositoryProtocol
from ...repositories.sale.sale_inventory_items import (
    SaleInventoryItemRepositoryProtocol,
)
from ...repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ...services.adapters.item_templates import ItemTemplateServiceProtocol

logger = logging.getLogger(__name__)


class PurchaseItemServiceProtocol(Protocol):
    async def purchase_item(
        self, inventory_item_id: uuid.UUID, buyer_character_id: uuid.UUID
    ) -> StatusOkSchema:
        """Покупка товара из sale."""
        ...


class PurchaseItemService(PurchaseItemServiceProtocol):
    def __init__(
        self,
        sale_repository: SaleInventoryItemRepositoryProtocol,
        character_item_repository: CharacterItemRepositoryProtocol,
        shop_repository: CityTradingShopCharacterRepositoryProtocol,
        city_settings_repository: CityTradingShopSettingsRepositoryProtocol,
        character_client: CharacterServiceClientProtocol,
        template_service: ItemTemplateServiceProtocol,
        items_events: ItemEventsProtocol,
        redis_publisher: RedisPublisherProtocol,
        sale_history_repository: SaleHistoryRepositoryProtocol,
    ):
        self.sale_repository = sale_repository
        self.character_item_repository = character_item_repository
        self.shop_repository = shop_repository
        self.city_settings_repository = city_settings_repository
        self.character_client = character_client
        self.template_service = template_service
        self.items_events = items_events
        self.redis_publisher = redis_publisher
        self.sale_history_repository = sale_history_repository

    async def purchase_item(
        self, inventory_item_id: uuid.UUID, buyer_character_id: uuid.UUID,
        amount: int | None = None
    ) -> StatusOkSchema:
        """Покупка товара из sale. Если amount задан — покупается часть."""
        sale_data = await self.sale_repository.get_sale_item_with_details(inventory_item_id)

        if sale_data is None:
            raise ItemNotForSaleError(item_id=inventory_item_id)

        sale_item, shop_id, item_weight_per_unit = sale_data

        # Проверка лицензии
        shop = await self.shop_repository.get(shop_id)
        if shop.end_license is None or shop.end_license < datetime.now(UTC):
            raise CityTradingShopLicenseExpiredError(
                location_slug=shop.location_slug,
                end_license=str(shop.end_license)
            )

        # Проверка количества
        if amount is not None and (amount < 1 or amount > sale_item.amount):
            from .....core.utils.exceptions import ValidationError
            raise ValidationError(
                field="amount",
                message=f"Cannot buy {amount}. On sale: {sale_item.amount}"
            )

        buy_full = amount is None or amount >= sale_item.amount
        buy_amount = sale_item.amount if buy_full else amount
        total_price = (sale_item.price * buy_amount).quantize(Decimal("0.01"))
        total_weight = item_weight_per_unit * buy_amount

        buyer = await self.character_client.get_simple_character_balance(buyer_character_id)
        if buyer.ducats < total_price:
            raise InsufficientDucatsToBuyError(
                required_ducats=total_price,
                current_ducats=buyer.ducats,
            )

        # ✅ НОВОЕ: Проверка веса покупателя перед покупкой
        weight_balance = await self.character_client.get_character_weight_balance(buyer_character_id)
        if weight_balance.weight + total_weight > weight_balance.max_weight:
            raise CharacterWeightExceededError(
                current_weight=int(weight_balance.weight),
                max_weight=int(weight_balance.max_weight),
            )

        seller_character_id = shop.character_id
        shop_settings = await self.city_settings_repository.get_by_location_and_level(
            shop.location_slug, shop.level,
        )

        if shop.location_slug == "1.27.trade-hall":
            source = "mining.trade_tent"
            op_payment = "tent_sale_payment"
            op_income = "tent_sale_income"
        else:
            source = f"mining.{shop.location_slug}"
            op_payment = "city_sale_payment"
            op_income = "city_sale_income"

        if buy_full:
            # Покупка всей строки целиком
            await self.sale_repository.delete(inventory_item_id)
            bought_item_id = inventory_item_id
        else:
            # Частичная покупка: отделяем часть, покупаем её
            bought_item_id = await self.character_item_repository.split_amount(
                inventory_item_id, buy_amount
            )
            await self.sale_repository.delete(bought_item_id)

        # Переносим товар покупателю
        await self.character_item_repository.transfer_item_to_buyer(
            bought_item_id, buyer_character_id
        )
        await self.character_item_repository.merge_identical_stack(bought_item_id)

        # Пересчитываем capacity из фактического содержимого
        await self.shop_repository.recalculate_capacity(shop_id)

        # Списываем дукаты покупателя
        operation_id_buyer = _uuid.uuid4()
        await self.character_client.debit_ducats(
            buyer_character_id,
            total_price,
            operation_id=operation_id_buyer,
            operation_type=op_payment,
            source=source,
            counterparty_id=seller_character_id,
            item_meta={
                "sale_id": str(sale_item.id),
                "inventory_item_id": str(sale_item.inventory_item_id),
                "item_slug": sale_item.item_slug,
                "price_per_unit": sale_item.price,
                "amount": buy_amount,
                "total_price": total_price,
            }
        )

        # Зачисляем продавцу полную сумму, налог списывается отдельно
        tax_amount = (total_price * Decimal(str(shop_settings.tax))).quantize(Decimal("0.01"))
        operation_id_seller_credit = _uuid.uuid4()
        await self.character_client.credit_ducats(
            seller_character_id,
            total_price,
            operation_id=operation_id_seller_credit,
            operation_type=op_income,
            source=source,
            counterparty_id=buyer_character_id,
            item_meta={
                "sale_id": str(sale_item.id),
                "item_slug": sale_item.item_slug,
                "price_per_unit": sale_item.price,
                "amount": buy_amount,
                "total_price": total_price,
                "tax": tax_amount,
            }
        )
        operation_id_tax = _uuid.uuid4()
        await self.character_client.debit_ducats(
            seller_character_id,
            tax_amount,
            operation_id=operation_id_tax,
            operation_type="tax",
            source=source,
            counterparty_id=None,
            item_meta={
                "sale_id": str(sale_item.id),
                "item_slug": sale_item.item_slug,
                "tax": tax_amount,
            }
        )

        # Пересчёт веса для обеих сторон сделки
        buyer_weight = await self.character_item_repository.get_total_weight(buyer_character_id)
        await self.character_client.update_weight(buyer_character_id, float(buyer_weight))

        seller_weight = await self.character_item_repository.get_total_weight(seller_character_id)
        await self.character_client.update_weight(seller_character_id, float(seller_weight))

        # Записываем в историю продаж
        try:
            await self.sale_history_repository.create(
                shop_id=shop_id,
                seller_character_id=seller_character_id,
                buyer_character_id=buyer_character_id,
                buyer_name=buyer.name,
                item_slug=sale_item.item_slug,
                item_name=sale_item.item_name,
                amount=buy_amount,
                price=total_price,
                tax=tax_amount,
                location_slug=shop.location_slug,
            )
        except Exception as e:
            # Не ломаем покупку если история не записалась
            import logging
            logging.getLogger(__name__).warning("Failed to write sale history: %s", e)

        buyer_message = self.template_service.get_item_purchase_buyer_message(
            location_slug=shop.location_slug,
            item_name=sale_item.item_name,
            price=f"{total_price:.2f}",
        )
        seller_message = self.template_service.get_item_purchase_seller_message(
            location_slug=shop.location_slug,
            item_name=sale_item.item_name,
            price=f"{total_price:.2f}",
            buyer_name=buyer.name,
            tax=f"{tax_amount:.2f}",
        )

        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="item_purchase_buyer",
                character_id=buyer_character_id,
                location_slug=shop.location_slug,
                content=buyer_message,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[buyer_character_id],                
            )
        )
        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="item_purchase_seller",
                character_id=seller_character_id,
                location_slug=shop.location_slug,
                content=seller_message,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[seller_character_id],                
            )
        )

        try:
            payload = {
                "event_type": "economy_state_updated", 
                "data": {
                    "action": "deal_completed",
                    "lot_id": str(inventory_item_id),
                    "shop_id": str(shop_id), 
                    "location_slug": shop.location_slug, 
                    "initiator_character_id": str(buyer_character_id),
                    "partner_character_id": str(seller_character_id)
                }
            }            
            await self.redis_publisher.publish("chat_room_private", payload)
        except Exception:            
            logger.exception("Failed to publish chat_room_private")

        return StatusOkSchema()