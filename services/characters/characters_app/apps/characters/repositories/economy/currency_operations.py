from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import CharacterCurrencyOperation
from ...schemas import CharacterCurrencyOperationFilters, CharacterCurrencyOperationListSchema


class CharacterCurrencyOperationRepositoryProtocol(Protocol):
    async def paginate(
        self,
        filters: CharacterCurrencyOperationFilters,
    ) -> CharacterCurrencyOperationListSchema: ...


class CharacterCurrencyOperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def paginate(
        self,
        filters: CharacterCurrencyOperationFilters,
    ) -> CharacterCurrencyOperationListSchema:
        query = select(CharacterCurrencyOperation)
        if filters.character_id is not None:
            query = query.where(CharacterCurrencyOperation.character_id == filters.character_id)
        if filters.operation_type is not None:
            query = query.where(CharacterCurrencyOperation.operation_type == filters.operation_type)
        if filters.source is not None:
            query = query.where(CharacterCurrencyOperation.source == filters.source)
        if filters.currency is not None:
            query = query.where(CharacterCurrencyOperation.currency == filters.currency.value)
        if filters.counterparty_id is not None:
            query = query.where(CharacterCurrencyOperation.counterparty_id == filters.counterparty_id)
        if filters.effective_from_date is not None:
            query = query.where(CharacterCurrencyOperation.created_at >= filters.effective_from_date)
        if filters.effective_to_date is not None:
            query = query.where(CharacterCurrencyOperation.created_at <= filters.effective_to_date)

        sort_column = {
            'created_at': CharacterCurrencyOperation.created_at,
        }[filters.sort_by.value]
        if filters.sort_order.value == 'asc':
            order_by = (sort_column.asc(), CharacterCurrencyOperation.id.asc())
        else:
            order_by = (sort_column.desc(), CharacterCurrencyOperation.id.desc())

        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.execute(
            query.order_by(*order_by).limit(filters.limit).offset(filters.offset)
        )
        return CharacterCurrencyOperationListSchema(
            objects=rows.scalars().all(),
            count=total or 0,
        )
