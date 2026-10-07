import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..items.enums import ItemType

ITEM_TYPE_LABELS = {
    ItemType.ELIXIR: "Эликсиры",
    ItemType.ANIMAL: "Животные",
    ItemType.OIL: "Масла",
    ItemType.FISH: "Рыба",
    ItemType.FURNITURE: "Мебель",
    ItemType.WEAPON: "Оружие",
    ItemType.SHIELD: "Щиты",
    ItemType.HELMET: "Броня: Шлемы",
    ItemType.ARMOR: "Броня: Доспехи",
    ItemType.GAUNTLETS: "Броня: Наручи",
    ItemType.GLOVES: "Броня: Перчатки",
    ItemType.LEGGINGS: "Броня: Поножи",
    ItemType.BOOTS: "Броня: Сандалии",
    ItemType.CLOAK: "Броня: Плащи",
    ItemType.AMULET: "Украшения: Амулеты",
    ItemType.PENDANT: "Украшения: Кулоны",
    ItemType.RING: "Украшения: Кольца",
}

RESOURCE_CATEGORY_LABELS = {
    "swamp": "Болото",
    "mine": "Шахта",
    "gems": "Прииск",
    "lake": "Озеро",
    "forest": "Лес",
    "sands": "Пески",
    "skins": "Шкуры",
}


class AdminCharacterSchema(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    location_slug: str | None = None
    is_online: bool


class AdminCharacterListSchema(BaseModel):
    objects: list[AdminCharacterSchema]
    count: int


class AdminCharacterDetailsSchema(AdminCharacterSchema):
    ducats: Decimal
    gold: Decimal


class AdminItemCatalogSchema(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    item_type: ItemType
    location_slug: str | None = None
    price: Decimal
    weight: int
    minimal_level: int
    is_stackable: bool

    model_config = {"from_attributes": True}


class AdminItemCatalogListSchema(BaseModel):
    objects: list[AdminItemCatalogSchema]
    count: int


class AdminInventoryItemSchema(BaseModel):
    id: uuid.UUID
    item_slug: str
    item_name: str
    item_type: ItemType
    amount: int
    wear: int | None = None
    expired_date: datetime | None = None
    is_expired: bool
    is_equipped: bool
    deal_id: uuid.UUID | None = None
    shop_id: uuid.UUID | None = None
    sale_price: Decimal | None = None


class AdminInventoryGroupsSchema(BaseModel):
    inventory: list[AdminInventoryItemSchema]
    shop: list[AdminInventoryItemSchema]
    sale: list[AdminInventoryItemSchema]
    deals: list[AdminInventoryItemSchema]


class AdminResourceSchema(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category: str | None
    weight: int
    price: int
    serial_number: int

    model_config = {"from_attributes": True}


class AdminResourceListSchema(BaseModel):
    objects: list[AdminResourceSchema]
    count: int


class AdminCharacterResourceSchema(BaseModel):
    resource_slug: str
    resource_name: str
    category: str | None
    amount: int


class AdminItemTypeSchema(BaseModel):
    item_type: ItemType
    readable_name: str


class AdminResourceCategorySchema(BaseModel):
    category: str
    readable_name: str


class AdminGiveItemSchema(BaseModel):
    item_slug: str = Field(max_length=128)
    amount: int = Field(gt=0)
    reason: str | None = None


class AdminTakeItemSchema(BaseModel):
    inventory_item_id: uuid.UUID | None = None
    item_slug: str | None = Field(None, max_length=128)
    amount: int = Field(gt=0)
    force: bool = False
    reason: str | None = None

    @model_validator(mode="after")
    def validate_item_selector(self) -> "AdminTakeItemSchema":
        if (self.inventory_item_id is None) == (self.item_slug is None):
            raise ValueError("Specify exactly one of inventory_item_id or item_slug")
        return self


class AdminResourceMutationSchema(BaseModel):
    resource_slug: str = Field(max_length=128)
    amount: int = Field(gt=0)
    reason: str | None = None


class AdminMoneyAddSchema(BaseModel):
    currency: Literal["ducats", "gold"]
    amount: Decimal = Field(gt=0)
    reason: str | None = None


class AdminMoneySetSchema(BaseModel):
    currency: Literal["ducats", "gold"]
    amount: Decimal = Field(ge=0)
    reason: str | None = None


class AdminMutationResultSchema(BaseModel):
    action: str
    character_id: uuid.UUID
    details: dict


class AdminLogSchema(BaseModel):
    id: uuid.UUID
    admin_user_id: uuid.UUID
    character_id: uuid.UUID
    action: str
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminLogListSchema(BaseModel):
    objects: list[AdminLogSchema]
    count: int
