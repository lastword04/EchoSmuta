from decimal import Decimal

BUYOUT_WEIGHT = Decimal("0.5")
LOCATIONS_WEIGHT = Decimal("0.3")
PLAYERS_WEIGHT = Decimal("0.2")
MAX_PRICE_CHANGE = Decimal("30")


def percentage_change(previous: Decimal, current: Decimal) -> Decimal:
    return Decimal("0") if previous == 0 else (current - previous) / previous * Decimal("100")


def calculate_inverse_price(old_price: Decimal, previous: dict[str, Decimal], current: dict[str, Decimal], min_price: Decimal | None = None, max_price: Decimal | None = None) -> Decimal:
    weighted_delta = (
        percentage_change(previous["BUYOUT"], current["BUYOUT"]) * BUYOUT_WEIGHT
        + percentage_change(previous["LOCATIONS"], current["LOCATIONS"]) * LOCATIONS_WEIGHT
        + percentage_change(previous["PLAYERS"], current["PLAYERS"]) * PLAYERS_WEIGHT
    ) / Decimal("2")
    weighted_delta = max(-MAX_PRICE_CHANGE, min(MAX_PRICE_CHANGE, weighted_delta))
    new_price = old_price * (Decimal("1") - weighted_delta / Decimal("100"))
    if min_price is not None:
        new_price = max(min_price, new_price)
    if max_price is not None:
        new_price = min(max_price, new_price)
    return new_price.quantize(Decimal("0.0001"))
