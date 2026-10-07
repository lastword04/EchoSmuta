from enum import Enum


class ItemType(str, Enum):
    ELIXIR = "elixir"
    ANIMAL = "animal"
    OIL = "oil"
    FISH = "fish"
    FURNITURE = "furniture"
    WEAPON = "weapon"
    SHIELD = "shield"
    HELMET = "helmet"
    ARMOR = "armor"
    GAUNTLETS = "gauntlets"
    GLOVES = "gloves"
    LEGGINGS = "leggings"
    BOOTS = "boots"
    CLOAK = "cloak"
    AMULET = "amulet"
    PENDANT = "pendant"
    RING = "ring"
    KIT = "kit"  


class EquipmentSlot(str, Enum):
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    GLOVES = "gloves"
    LEGS = "legs"
    FEET = "feet"
    WEAPON = "weapon"
    SHIELD = "shield"
    CLOAK = "cloak"
    AMULET = "amulet"
    PENDANT = "pendant"
    RING1 = "ring1"
    RING2 = "ring2"
    RING3 = "ring3"


class ItemBindingType(str, Enum):
    NONE = "none"
    CHARACTER = "character"
    CLAN = "clan"


class AnimalTransportType(str, Enum):
    LAND = "land"
    AIR = "air"


class ItemCreatingStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
