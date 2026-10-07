from enum import Enum
from typing_extensions import Self

class Currency(str, Enum):
    DUCATS = "ducats"
    GOLD = "gold"

    def opposite(self: Self) -> Self:
        return Currency.GOLD if self == Currency.DUCATS else Currency.DUCATS
    
