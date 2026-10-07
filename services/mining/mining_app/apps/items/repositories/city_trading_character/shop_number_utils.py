"""Утилиты для работы с нумерацией магазинов по локациям"""
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import ShopNumberCounter


async def get_next_shop_number(session: AsyncSession, location_slug: str) -> int:
    """
    Атомарно получает следующий доступный номер магазина для указанной локации.
    
    Использует UPSERT (INSERT ... ON CONFLICT DO UPDATE) для атомарной операции:
    - Если запись для локации не существует, создает её с last_number=1
    - Если запись существует, инкрементирует last_number на 1
    
    Args:
        session: Активная сессия SQLAlchemy (должна быть внутри транзакции)
        location_slug: Идентификатор локации
        
    Returns:
        int: Следующий доступный номер магазина для данной локации
        
    Note:
        Функция должна вызываться внутри транзакции создания магазина.
        В случае отката транзакции номер останется "зарезервированным",
        что может привести к разрывам в нумерации (это допустимо).
    """
    # Используем PostgreSQL-специфичный INSERT ... ON CONFLICT
    # location_slug является PRIMARY KEY (через переопределение id в модели)
    # Используем имя constraint вместо index_elements
    stmt = insert(ShopNumberCounter).values(
        id=location_slug,  # id переопределён как location_slug в модели
        last_number=1
    ).on_conflict_do_update(
        constraint='shop_number_counters_pkey',  # PRIMARY KEY constraint
        set_={'last_number': ShopNumberCounter.last_number + 1}
    ).returning(ShopNumberCounter.last_number)
    
    result = await session.execute(stmt)
    next_number = result.scalar_one()
    
    return next_number
