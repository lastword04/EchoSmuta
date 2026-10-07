import logging
from datetime import UTC, datetime

import sqlalchemy as sa

from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from ..enums import ItemType
from ..events.items_sync import ItemEventsSyncAdapter
from ..models import CityTradingShop, InventoryItem, Item, SaleInventoryItem
from ..services.adapters.item_templates import ItemTemplateServiceProtocol

logger = logging.getLogger(__name__)


class CleanupExpiredItemsSyncUseCase:
    def __init__(
        self,
        items_events: ItemEventsSyncAdapter,
        template_service: ItemTemplateServiceProtocol,
    ):
        self.items_events = items_events
        self.template_service = template_service

    def __call__(self, session, limit: int = 100) -> int:
        """
        Находит и удаляет все истёкшие предметы из инвентаря и магазинов.
        Отправляет системные сообщения владельцам.

        Возвращает количество удалённых предметов.
        """
        from ..repositories.city_trading_character.city_trading_shop_sync import (
            CityTradingShopSyncRepository,
        )

        now = datetime.now(UTC)
        shop_repo = CityTradingShopSyncRepository(session)

        # Находим все истёкшие предметы (в инвентаре ИЛИ в магазине)
        stmt = (
            sa.select(InventoryItem, Item)
            .join(Item, InventoryItem.item_slug == Item.slug)
            .where(
                InventoryItem.expired_date.isnot(None),
                InventoryItem.expired_date < now,
                sa.or_(
                    InventoryItem.character_id.isnot(None),
                    InventoryItem.shop_id.isnot(None),
                ),
            )
            .limit(limit)
        )

        results = session.execute(stmt).all()
        deleted_count = 0

        for inventory_item, item in results:
            try:
                # СНАЧАЛА собираем все данные из объекта (пока он не удалён)
                item_id = inventory_item.id
                item_name = item.name
                item_weight = item.weight
                item_amount = inventory_item.amount
                item_character_id = inventory_item.character_id
                item_shop_id = inventory_item.shop_id
                
                # Определяем type сообщения
                if item.item_type == ItemType.ANIMAL:
                    message_content = self.template_service.get_animal_died_message(item_name)
                    event_type = "animal_died"
                else:
                    message_content = self.template_service.get_item_expired_message(item_name, item_amount)  
                    event_type = "item_expired"

                # Определяем recipient и location
                if item_character_id:
                    target_id = item_character_id
                    location_slug = item.location_slug
                elif item_shop_id:
                    shop = shop_repo.get_by_id(item_shop_id)
                    if not shop:
                        logger.warning(f"Shop {item_shop_id} not found, skipping item {item_id}")
                        # Возвращаем вместимость на 0 если магазин не найден
                        session.execute(
                            sa.delete(SaleInventoryItem).where(
                                SaleInventoryItem.inventory_item_id == item_id
                            )
                        )
                        session.delete(inventory_item)
                        deleted_count += 1
                        continue
                    target_id = shop.character_id
                    location_slug = shop.location_slug
                else:
                    continue

                # Отправляем системное сообщение
                self.items_events.publish_message(ItemMessageEventSchema(
                    event_type=event_type,
                    character_id=target_id,
                    location_slug=location_slug,
                    content=message_content,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[target_id],
                    is_trade=False,
                ))

                # ВОЗВРАЩАЕМ ВМЕСТИМОСТЬ ЛАВКЕ (до удаления)
                if item_shop_id:
                    session.execute(
                        sa.update(CityTradingShop)
                        .where(CityTradingShop.id == item_shop_id)
                        .values(
                            current_capacity=sa.func.greatest(
                                CityTradingShop.current_capacity - (item_weight * item_amount),
                                0
                            )
                        )
                    )

                # УДАЛЯЕМ ЗАПИСЬ ИЗ sale_inventory_items (если была на продаже)
                session.execute(
                    sa.delete(SaleInventoryItem).where(
                        SaleInventoryItem.inventory_item_id == item_id
                    )
                )

                # Удаляем сам предмет
                session.delete(inventory_item)
                deleted_count += 1

                logger.info(
                    f"Deleted expired item: {item_name} (id={item_id}) "
                    f"for character {target_id}"
                )

            except Exception:
                logger.exception(f"Failed to process expired item {inventory_item.id}")
                continue

        session.commit()
        return deleted_count