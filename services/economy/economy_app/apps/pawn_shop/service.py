import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CurrentPrice, ExchangeLot, ExchangeLotItem, LotStatus, Resource, ResourceSourceType


def ensure_tradeable(resource: Resource) -> None:
    if not resource.is_tradeable or resource.source_type is not ResourceSourceType.RESOURCE_LOCATION:
        raise HTTPException(status_code=400, detail="Resource is not tradeable")


async def get_resource(session: AsyncSession, resource_id: uuid.UUID) -> Resource:
    resource = await session.scalar(select(Resource).where(Resource.id == resource_id))
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    ensure_tradeable(resource)
    return resource


async def get_price(session: AsyncSession, resource_id: uuid.UUID) -> CurrentPrice:
    price = await session.scalar(select(CurrentPrice).where(CurrentPrice.resource_id == resource_id).with_for_update())
    if price is None:
        raise HTTPException(status_code=409, detail="Resource price is not initialized")
    return price


async def list_lots(session: AsyncSession, resource_id: uuid.UUID | None = None) -> list[ExchangeLot]:
    query = (
        select(ExchangeLot)
        .where(ExchangeLot.status == LotStatus.ACTIVE)
        .order_by(ExchangeLot.created_at.desc())
    )
    if resource_id is not None:
        # Фильтр по ресурсу — через позиции бандла
        query = query.where(
            ExchangeLot.id.in_(
                select(ExchangeLotItem.lot_id).where(ExchangeLotItem.resource_id == resource_id)
            )
        )
    return list((await session.scalars(query)).all())