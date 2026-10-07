import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func

from ...core.db import Session
from ..pawn_shop.models import BuyoutStock, CurrentPrice, EconomyTransaction, Resource, TransactionType
from ..pawn_shop.scheduler import run_scheduled_price_recalculation
from .depends import get_admin_mutation_service, require_admin
from .schemas import (
    AdminForceRecalculationRequest,
    AdminSetPriceRequest,
    AdminStockRequest,
    AdminUpdateResourceRequest,
    AdminResourceRead,
    AdminTransactionRead,
)
from .services.admin_mutations import AdminMutationService

router = APIRouter(
    prefix="/api/economy/admin",
    tags=["Economy Admin"],
    dependencies=[Depends(require_admin)],
)


@router.post("/resources/{resource_id}/stock")
async def admin_stock(
    resource_id: uuid.UUID,
    data: AdminStockRequest,
    service: AdminMutationService = Depends(get_admin_mutation_service),
) -> dict:
    return await service.set_stock(resource_id, data)


@router.post("/resources/{resource_id}/prices")
async def admin_set_prices(
    resource_id: uuid.UUID,
    data: AdminSetPriceRequest,
    service: AdminMutationService = Depends(get_admin_mutation_service),
) -> dict:
    return await service.set_prices(resource_id, data)


@router.patch("/resources/{resource_id}")
async def admin_update_resource(
    resource_id: uuid.UUID,
    data: AdminUpdateResourceRequest,
    service: AdminMutationService = Depends(get_admin_mutation_service),
) -> dict:
    return await service.update_resource(resource_id, data)


@router.post("/prices/recalculate")
async def admin_force_recalculate_prices(
    data: AdminForceRecalculationRequest,
) -> dict:
    await run_scheduled_price_recalculation(force=data.force)
    return {"status": "started_or_completed"}


@router.get("/resources", response_model=list[AdminResourceRead])
async def admin_resources(session: Session) -> list[AdminResourceRead]:
    rows = await session.execute(
        select(Resource, CurrentPrice, BuyoutStock)
        .outerjoin(CurrentPrice, CurrentPrice.resource_id == Resource.id)
        .outerjoin(BuyoutStock, BuyoutStock.resource_id == Resource.id)
        .order_by(Resource.order)
    )
    result = []
    for r, p, s in rows.all():
        result.append(AdminResourceRead(
            id=r.id,
            code=r.code,
            name=r.name,
            category=r.category.value if hasattr(r.category, 'value') else str(r.category),       
            base_sell_price=r.base_sell_price,
            base_buy_price=r.base_buy_price,
            min_sell_price=r.min_sell_price,
            max_sell_price=r.max_sell_price,
            min_buy_price=r.min_buy_price,
            max_buy_price=r.max_buy_price,
            sell_price=p.sell_price if p else None,
            buy_price=p.buy_price if p else None,
            stock_quantity=s.quantity if s else 0,
            next_recalculation_at=p.next_recalculation_at if p else None,
        ))
    return result


@router.get("/transactions", response_model=list[AdminTransactionRead])
async def admin_transactions(
    session: Session,
    limit: int = Query(50, ge=1, le=500), # увеличил лимит до 500
    offset: int = Query(0, ge=0),
    resource_id: uuid.UUID | None = Query(None),
    transaction_type: TransactionType | None = Query(None),
    character_id: uuid.UUID | None = Query(None, description="Filter by buyer_id OR seller_id"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
) -> list[AdminTransactionRead]:
    query = select(EconomyTransaction)
    
    # Фильтр по игроку (участвовал как покупатель ИЛИ продавец)
    if character_id is not None:
        query = query.where(
            (EconomyTransaction.buyer_id == character_id) | 
            (EconomyTransaction.seller_id == character_id)
        )
    if resource_id is not None:
        query = query.where(EconomyTransaction.resource_id == resource_id)
    if transaction_type is not None:
        query = query.where(EconomyTransaction.transaction_type == transaction_type)
    
    # Фильтры по дате
    if start_date is not None:
        query = query.where(EconomyTransaction.created_at >= start_date)
    if end_date is not None:
        # Добавляем 1 день, чтобы включить весь последний день (до 23:59:59)
        query = query.where(EconomyTransaction.created_at <= end_date + timedelta(days=1))
        
    query = query.order_by(EconomyTransaction.created_at.desc()).limit(limit).offset(offset)
    rows = await session.scalars(query)
    return list(rows.all())


@router.get("/statistics")
async def admin_statistics(
    session: Session,
    start_date: datetime = Query(..., description="Начало периода (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="Конец периода (YYYY-MM-DD)"),
) -> dict:
    # end_date_inclusive включает весь последний день до 23:59:59
    end_date_inclusive = end_date + timedelta(days=1)
    
    # 1. Общие цифры
    res_totals = await session.execute(
        select(
            func.count(EconomyTransaction.id), 
            func.coalesce(func.sum(EconomyTransaction.total), 0)
        ).where(
            EconomyTransaction.created_at >= start_date,
            EconomyTransaction.created_at < end_date_inclusive
        )
    )
    total_count, total_volume = res_totals.one()
    
    # 2. Распределение по типам
    res_types = await session.execute(
        select(EconomyTransaction.transaction_type, func.count(EconomyTransaction.id))
        .where(
            EconomyTransaction.created_at >= start_date, 
            EconomyTransaction.created_at < end_date_inclusive
        )
        .group_by(EconomyTransaction.transaction_type)
    )
    by_type = {t.name: c for t, c in res_types.all()}
    
    # 3. Топ-5 ресурсов по обороту
    res_top = await session.execute(
        select(
            Resource.name, 
            func.coalesce(func.sum(EconomyTransaction.total), 0).label('vol'), 
            func.count(EconomyTransaction.id).label('cnt')
        )
        .join(EconomyTransaction, Resource.id == EconomyTransaction.resource_id)
        .where(
            EconomyTransaction.created_at >= start_date, 
            EconomyTransaction.created_at < end_date_inclusive
        )
        .group_by(Resource.id, Resource.name)
        .order_by(func.sum(EconomyTransaction.total).desc())
        .limit(5)
    )
    top_resources = [
        {"name": name, "volume": float(vol), "count": cnt} 
        for name, vol, cnt in res_top.all()
    ]
    
    return {
        "total_transactions": total_count,
        "total_volume": float(total_volume),
        "by_type": by_type,
        "top_resources": top_resources
    }