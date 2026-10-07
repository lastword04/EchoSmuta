import uuid
from typing import Any
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from fastapi import HTTPException
import logging

from .....core.clients.characters_client import CharactersClient
from .....core.clients.mining_client import MiningClient
from ...models import BuyoutStock, EconomyTransaction, TransactionType
from ...schemas import BulkTradeRequest
from ...service import get_price, get_resource
from ...events.economy import EconomyEventsProtocol
from ...services.economy_templates import EconomyTemplateServiceProtocol
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope
from shared.utils.plural import plural
from .buy import BuyResourceFromBuyoutUseCase

logger = logging.getLogger(__name__)


class BuyResourcesBulkUseCase:
    def __init__(self, buy_use_case: BuyResourceFromBuyoutUseCase) -> None:
        self.buy_use_case = buy_use_case

    async def __call__(
        self,
        data: BulkTradeRequest,
        character_id: uuid.UUID,
        session: AsyncSession
    ) -> list[dict[str, Any]]:
        """Покупает несколько ресурсов одним запросом с ОДНИМ сообщением."""
        results = []
        total_price = Decimal("0")
        resources_parts = []

        # 0. Склеиваем дубликаты: суммируем количества по каждому ресурсу
        aggregated: dict[uuid.UUID, int] = {}
        for item in data.items:
            if item.quantity <= 0:
                raise HTTPException(status_code=422, detail="Количество должно быть больше нуля")
            aggregated[item.resource_id] = aggregated.get(item.resource_id, 0) + item.quantity

        # 1. Проверяем наличие в скупке и собираем цены
        items_data = []
        for resource_id, quantity in aggregated.items():
            resource = await get_resource(session, resource_id)
            price = await get_price(session, resource.id)
            stock = await session.scalar(
                select(BuyoutStock).where(BuyoutStock.resource_id == resource.id).with_for_update()
            )
            if stock is None or stock.quantity < quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ресурса {resource.name} нет в скупке в нужном количестве"
                )

            item_total_price = (quantity * price.sell_price).quantize(Decimal("0.01"))
            total_price += item_total_price
            resources_parts.append(
                f"{quantity} {plural(quantity, 'брикет', 'брикета', 'брикетов')} ресурса {resource.name}"
            )
            items_data.append({
                "resource": resource,
                "price": price,
                "quantity": quantity,
                "item_total": item_total_price,
            })

        # 2. Проверяем баланс игрока
        balance = await self.buy_use_case.characters_client.get_balance(character_id)
        if balance < total_price:
            raise HTTPException(status_code=409, detail="Недостаточно дукатов.")

        # 3. Списываем дукаты одной транзакцией
        op_debit = uuid.uuid4()
        op_refund = uuid.uuid5(op_debit, "refund")
        try:
            await self.buy_use_case.characters_client.debit(
                character_id, total_price,
                operation_id=op_debit,
                operation_type="buyout_purchase_bulk",
                source="economy.buyout",
                item_meta={"items_count": len(items_data)},
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                raise HTTPException(status_code=409, detail="External service rejected buyout bulk buy operation") from exc
            raise HTTPException(status_code=502, detail="External service error") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        # 4. Начисляем каждый ресурс с компенсацией при сбое
        credited: list[tuple[str, int, uuid.UUID]] = []
        for row in items_data:
            resource = row["resource"]
            quantity = row["quantity"]
            item_total = row["item_total"]
            price = row["price"]

            op_credit = uuid.uuid5(op_debit, f"credit-{resource.code}")
            try:
                await self.buy_use_case.mining_client.credit(
                    resource.code, character_id, quantity, op_credit
                )
                credited.append((resource.code, quantity, op_credit))
            except (httpx.HTTPStatusError, httpx.HTTPError) as exc:
                # Откатить все уже начисленные
                for code, qty, cop in credited:
                    try:
                        await self.buy_use_case.mining_client.debit(code, character_id, qty, uuid.uuid5(cop, "rollback"))
                    except Exception as re:
                        logger.error("Rollback credit failed for %s: %s", code, re)
                # Refund общего дебит
                try:
                    await self.buy_use_case.characters_client.credit(
                        character_id, total_price,
                        operation_id=op_refund,
                        operation_type="buyout_purchase_bulk_refund",
                        source="economy.buyout",
                        item_meta={"compensates": str(op_debit)},
                    )
                except Exception as re:
                    logger.error("Refund bulk debit failed: %s", re)
                raise HTTPException(status_code=502, detail="External service error during bulk buy") from exc

            stock = await session.scalar(
                select(BuyoutStock).where(BuyoutStock.resource_id == resource.id).with_for_update()
            )
            stock.quantity -= quantity

            transaction = EconomyTransaction(
                transaction_type=TransactionType.BUYOUT_BUY,
                resource_id=resource.id,
                quantity=quantity,
                price_per_unit=price.sell_price,
                total=item_total,
                buyer_id=character_id,
                seller_id=None,
                lot_id=None,
            )
            session.add(transaction)

            results.append({
                "resource_id": resource.id,
                "quantity": quantity,
                "price_per_unit": price.sell_price,
                "total_price": item_total,
                "operation_id": op_credit,
            })            

        # 4.5. Сохраняем изменения стока и транзакций в БД
        await session.commit()   

        # 5. ОДНО агрегированное сообщение
        try:
            location_slug = await self.buy_use_case.characters_client.get_character_location(character_id)
        except Exception:
            location_slug = "unknown"

        try:
            items_list = ", ".join(resources_parts)
            message_text = self.buy_use_case.template_service.get_buyout_buy_message(
                items_list=items_list,
                price=str(total_price),
            )
            await self.buy_use_case.economy_events.publish_message(
                ItemMessageEventSchema(
                    event_type="economy_buyout_buy",
                    character_id=character_id,
                    location_slug=location_slug,
                    content=message_text,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character_id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_buy event: {e}")

        try:
            await self.buy_use_case.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "buyout_stock_updated",
                    "location_slug": location_slug,   
                    "initiator_character_id": str(character_id),
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_stock_updated: {e}")

        return results