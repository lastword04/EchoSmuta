import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....settings import settings
from ...pawn_shop.service import get_price
from ...pawn_shop.events.economy import EconomyEventsProtocol 
from ..repositories.admin_mutations import AdminMutationsRepository
from ..schemas import AdminStockRequest, AdminSetPriceRequest, AdminUpdateResourceRequest
import logging

logger = logging.getLogger(__name__)


class AdminMutationService:
    def __init__(self, session: AsyncSession, economy_events: EconomyEventsProtocol) -> None:
        self.session = session
        self.repo = AdminMutationsRepository(session)
        self.economy_events = economy_events

    async def set_stock(self, resource_id: uuid.UUID, data: AdminStockRequest) -> dict:
        stock = await self.repo.get_stock_for_update(resource_id)
        if stock is None:
            stock = await self.repo.create_stock(resource_id, data.quantity)
        else:
            stock.quantity = data.quantity

        response: dict = {"resource_id": resource_id, "quantity": data.quantity}

        # Обновляем базовые цены и пересчитываем границы
        if data.base_sell_price is not None or data.base_buy_price is not None:
            resource = await self.repo.get_resource_for_update(resource_id)
            if resource is None:
                raise HTTPException(status_code=404, detail="Resource not found")

            if data.base_sell_price is not None:
                resource.base_sell_price = data.base_sell_price
                resource.min_sell_price = (
                    data.base_sell_price * Decimal(str(settings.pricing.price_floor_multiplier))
                ).quantize(Decimal("0.01"))
                resource.max_sell_price = (
                    data.base_sell_price * Decimal(str(settings.pricing.price_ceiling_multiplier))
                ).quantize(Decimal("0.01"))

            if data.base_buy_price is not None:
                resource.base_buy_price = data.base_buy_price
                resource.min_buy_price = (
                    data.base_buy_price * Decimal(str(settings.pricing.price_floor_multiplier))
                ).quantize(Decimal("0.01"))
                resource.max_buy_price = (
                    data.base_buy_price * Decimal(str(settings.pricing.price_ceiling_multiplier))
                ).quantize(Decimal("0.01"))

            response.update({
                "base_sell_price": resource.base_sell_price,
                "base_buy_price": resource.base_buy_price,
                "min_sell_price": resource.min_sell_price,
                "max_sell_price": resource.max_sell_price,
                "min_buy_price": resource.min_buy_price,
                "max_buy_price": resource.max_buy_price,
            })

        self.repo.log_admin_action(resource_id, data.quantity, Decimal("0"))
        await self.session.commit()
        try:
            await self.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "buyout_stock_updated",
                    "location_slug": settings.pawn_shop_location_slug,
                    "initiator_character_id": None,
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_stock_updated: {e}")
        return response

    async def set_prices(self, resource_id: uuid.UUID, data: AdminSetPriceRequest) -> dict:
        price = await get_price(self.session, resource_id)

        if data.sell_price is not None:
            price.previous_sell_price = price.sell_price
            price.sell_price = data.sell_price
        if data.buy_price is not None:
            price.previous_buy_price = price.buy_price
            price.buy_price = data.buy_price

        price.last_recalculated_at = datetime.now(timezone.utc)
        self.repo.log_admin_action(resource_id, 0, price.sell_price)
        await self.session.commit()
        try:
            await self.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "buyout_prices_updated",
                    "location_slug": settings.pawn_shop_location_slug,
                    "initiator_character_id": None,
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_prices_updated: {e}")
        return {
            "resource_id": resource_id,
            "sell_price": price.sell_price,
            "buy_price": price.buy_price,
        }

    async def update_resource(self, resource_id: uuid.UUID, data: AdminUpdateResourceRequest) -> dict:
        resource = await self.repo.get_resource_for_update(resource_id)
        if resource is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(resource, field, value)
        self.repo.log_admin_action(resource_id, 0, resource.base_sell_price)
        await self.session.commit()
        return {"resource_id": resource_id, "updated": update_data}