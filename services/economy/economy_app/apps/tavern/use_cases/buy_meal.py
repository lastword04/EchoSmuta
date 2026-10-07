import uuid
import httpx
import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope
from ...pawn_shop.events.economy import EconomyEventsProtocol
from ...pawn_shop.services.economy_templates import EconomyTemplateServiceProtocol
from ....core.clients.characters_client import CharactersClient
from ....settings import settings
from ...pawn_shop.models import EconomyTransaction, TransactionType
from ..models import TavernMeal
from ..rotation import ensure_stock_rotation

logger = logging.getLogger(__name__)


class BuyMealUseCase:
    def __init__(
        self, 
        characters_client: CharactersClient,
        economy_events: EconomyEventsProtocol,
        template_service: EconomyTemplateServiceProtocol,
    ) -> None:
        self.characters_client = characters_client
        self.economy_events = economy_events
        self.template_service = template_service

    async def __call__(self, meal_id: uuid.UUID, character_id: uuid.UUID, session: AsyncSession) -> dict:
        # 1. Ленивая ротация стока
        await ensure_stock_rotation(session)

        # 2. Найти блюдо по meal_id (с блокировкой строки)
        meal = await session.scalar(
            select(TavernMeal).where(TavernMeal.id == meal_id).with_for_update()
        )

        # 3. Если блюда нет или оно неактивно
        if meal is None or not meal.is_active:
            raise HTTPException(status_code=404, detail="Блюдо не найдено.")

        # 4. Если порций нет — отказ до списания денег
        if meal.stock <= 0:
            raise HTTPException(status_code=409, detail="Этого блюда нет в наличии.")

        # 5. Проверить, что персонаж находится в Харчевне
        location_slug = await self.characters_client.get_character_location(character_id)
        if location_slug != settings.tavern_location_slug:
            raise HTTPException(status_code=400, detail="Вы находитесь не в Харчевне.")

        # 6. Списать дукаты
        operation_id = uuid.uuid4()
        op_debit = uuid.uuid5(operation_id, "debit")
        op_refund = uuid.uuid5(operation_id, "refund")
        
        try:
            await self.characters_client.debit(
                character_id,
                meal.ducats_price,
                operation_id=op_debit,
                operation_type="tavern_purchase",
                source="economy.tavern",
                item_meta={"meal_id": str(meal.id), "meal_slug": meal.slug},
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                raise HTTPException(status_code=409, detail="Недостаточно дукатов.")
            raise HTTPException(status_code=502, detail="Ошибка при списании дукатов.")
        except httpx.HTTPError:
            raise HTTPException(status_code=502, detail="Сервис персонажей недоступен.")

        # 7. Применить эффекты еды; любая ошибка → компенсирующий возврат дукатов
        effects: list[dict] = []
        if meal.health_restore > 0:
            effects.append({"effect_type": "hp_restore", "value": meal.health_restore})
        if meal.tiredness_restore_percent > 0:
            effects.append({"effect_type": "stamina_restore_percent", "value": meal.tiredness_restore_percent})
        try:
            await self.characters_client.consume_food(
                character_id,
                effects,
                cooldown_seconds=900,
                required_location_slug=settings.tavern_location_slug,
            )
        except Exception:
            await self.characters_client.credit(
                character_id,
                meal.ducats_price,
                operation_id=op_refund,
                operation_type="tavern_purchase_refund",
                source="economy.tavern",
                item_meta={"compensates": str(op_debit)},
            )
            raise

        # 8. Уменьшить сток порций
        meal.stock -= 1

        # 9. Записать транзакцию (resource_id не используется для таверны — колонка nullable)
        session.add(EconomyTransaction(
            transaction_type=TransactionType.TAVERN_BUY,
            quantity=1,
            price_per_unit=meal.ducats_price,
            total=meal.ducats_price,
            buyer_id=character_id,
            seller_id=None,
            lot_id=None,
        ))

        # Получаем локацию персонажа для события
        try:
            location_slug = await self.characters_client.get_character_location(character_id)
        except Exception as e:
            logger.warning(f"Failed to get character location: {e}")
            location_slug = "unknown"

        # Публикуем событие в чат
        try:
            message_text = self.template_service.get_tavern_buy_message(
                meal_name=meal.name,
                price=str(meal.ducats_price),
            )
            await self.economy_events.publish_message(
                ItemMessageEventSchema(
                    event_type="economy_tavern_buy",
                    character_id=character_id,
                    location_slug=location_slug,
                    content=message_text,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character_id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish tavern_buy event: {e}")

        # 10. Commit и ответ
        await session.commit()
        return {"status": "ok", "meal_name": meal.name}

