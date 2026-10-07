from decimal import Decimal

import httpx
from fastapi import HTTPException


def total_price(quantity: Decimal, price_per_unit: Decimal) -> Decimal:
    return (quantity * price_per_unit).quantize(Decimal("0.01"))


def raise_external_error(exc: httpx.HTTPStatusError, detail: str) -> None:
    if exc.response.status_code == 409:
        raise HTTPException(status_code=409, detail=detail) from exc
    if exc.response.status_code == 404:
        raise HTTPException(status_code=404, detail=detail) from exc
    raise HTTPException(status_code=502, detail="External service error") from exc

def split_bundle_price(price, items, resource_map) -> dict:
    """Распределяет цену бандла пропорционально базовым ценам ресурсов."""
    weights = [(item, resource_map[item.resource_id].base_sell_price * item.quantity) for item in items]
    total_weight = sum((w for _, w in weights), Decimal(0))

    result = {}
    allocated = Decimal("0")
    for idx, (item, weight) in enumerate(weights):
        if idx == len(weights) - 1:
            share = price - allocated  # последняя позиция добивает до точной суммы
        elif total_weight > 0:
            share = (price * weight / total_weight).quantize(Decimal("0.01"))
        else:
            share = (price / len(weights)).quantize(Decimal("0.01"))
        result[item.resource_id] = share
        allocated += share
    return result