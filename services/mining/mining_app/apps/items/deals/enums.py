from enum import Enum

from ..enums import ItemType


class DealStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETING = "COMPLETING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class DealAssetType(str, Enum):
    RESOURCE = "RESOURCE"
    INVENTORY_ITEM = "INVENTORY_ITEM"


class ResourceReservationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    TRANSFERRED = "TRANSFERRED"


class DealLedgerOperationKind(str, Enum):
    ESCROW_HOLD = "ESCROW_HOLD"
    ESCROW_RELEASE = "ESCROW_RELEASE"
    TRANSFER = "TRANSFER"
    TAX = "TAX"
    COMPENSATION = "COMPENSATION"


class DealLedgerOperationStatus(str, Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"
    COMPENSATED = "COMPENSATED"
    FAILED = "FAILED"


class DealCurrency(str, Enum):
    DUCATS = "DUCATS"
    GOLD = "GOLD"


TRADEABLE_ITEM_TYPES: frozenset[ItemType] = frozenset(
    {
        ItemType.ELIXIR,
        ItemType.ANIMAL,
        ItemType.OIL,
        ItemType.FISH,
        ItemType.FURNITURE,
        ItemType.WEAPON,
        ItemType.SHIELD,
        ItemType.HELMET,
        ItemType.ARMOR,
        ItemType.GAUNTLETS,
        ItemType.GLOVES,
        ItemType.LEGGINGS,
        ItemType.BOOTS,
        ItemType.CLOAK,
        ItemType.AMULET,
        ItemType.PENDANT,
        ItemType.RING,
        ItemType.KIT,
    }
)
