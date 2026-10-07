from decimal import Decimal

from ..exceptions import SalePriceTooLowError

MIN_PRICE_RATIO = Decimal("0.5")

def validate_sale_price(base_price: Decimal, requested_price: Decimal) -> None:
    """Проверяет, что цена продажи не ниже половины базовой."""
    if base_price <= 0:
        return
    min_allowed = base_price * MIN_PRICE_RATIO
    if requested_price < min_allowed:
        raise SalePriceTooLowError(min_price=min_allowed)