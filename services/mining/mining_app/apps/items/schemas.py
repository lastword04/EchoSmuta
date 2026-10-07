import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from shared.enums import Race, ResultStatus
from shared.schemas.base import CreateBaseModel, TimestampMixin, UpdateBaseModel
from shared.schemas.files import FileReadSchema

from .enums import EquipmentSlot, ItemBindingType, ItemCreatingStatus, ItemType


class ItemBaseSchema(BaseModel):
    name: str
    slug: str
    item_type: ItemType
    location_slug: str
    price: Decimal
    weight: int
    race: Race | None = None
    parameters: dict | None = None
    ability_parameters: dict | None = None
    craft_stages: int | None = None
    craft_experience: int | None = None
    min_shelf_life_days: int | None = None
    max_shelf_life_days: int | None = None
    min_output_quantity: int | None = None
    max_output_quantity: int | None = None
    minimal_level: int
    is_stackable: bool
    can_sell: bool

class ItemCreateSchema(ItemBaseSchema, CreateBaseModel):
    pass

class ItemUpdateSchema(ItemBaseSchema, UpdateBaseModel):
    pass

class ItemReadSchema(ItemBaseSchema, TimestampMixin):
    id: uuid.UUID

class ResourceItemReadSchema(ItemReadSchema):
    recipe_price: Decimal | None = None


class ItemComponentBaseSchema(BaseModel):
    item_slug: str
    resource_slug: str
    quantity: int

class ItemComponentCreateSchema(ItemComponentBaseSchema, CreateBaseModel):
    pass

class ItemComponentUpdateSchema(ItemComponentBaseSchema, UpdateBaseModel):
    pass

class ItemComponentReadSchema(ItemComponentBaseSchema, TimestampMixin):
    pass


class ItemPriceBaseSchema(BaseModel):
    item_slug: str
    price: Decimal
    quantity: int

class ItemPriceCreateSchema(ItemPriceBaseSchema, CreateBaseModel):
    pass

class ItemPriceUpdateSchema(ItemPriceBaseSchema, UpdateBaseModel):
    pass

class ItemPriceReadSchema(ItemPriceBaseSchema, TimestampMixin):
    id: uuid.UUID


class CityTradingShopSettingsBaseSchema(BaseModel):
    location_slug: str
    level: int = 0
    capacity: int
    tax: float
    price_up_level: int | None

class CityTradingShopSettingsCreateSchema(CityTradingShopSettingsBaseSchema, CreateBaseModel):
    pass

class CityTradingShopSettingsUpdateSchema(CityTradingShopSettingsBaseSchema, UpdateBaseModel):
    pass

class CityTradingShopSettingsReadSchema(CityTradingShopSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID

class CityTradingShopBuySettingsBaseSchema(BaseModel):
    location_slug: str
    min_level: int = 0
    price: Decimal

class CityTradingShopBuySettingsCreateSchema(CityTradingShopBuySettingsBaseSchema, CreateBaseModel):
    pass

class CityTradingShopBuySettingsUpdateSchema(CityTradingShopBuySettingsBaseSchema, UpdateBaseModel):
    pass

class CityTradingShopBuySettingsReadSchema(CityTradingShopBuySettingsBaseSchema, TimestampMixin):
    id: uuid.UUID

class CityTradingShopBaseSchema(BaseModel):
    location_slug: str
    character_id: uuid.UUID | None = None
    character_name: str | None = None
    name: str
    description: str | None = None
    level: int = 0
    current_capacity: int = 0
    photo_id: uuid.UUID | None = None
    end_license: datetime | None = None

class CityTradingShopCreateSchema(CityTradingShopBaseSchema, CreateBaseModel):
    pass

class CityTradingShopUpdateSchema(CityTradingShopBaseSchema, UpdateBaseModel):
    pass

class CityTradingShopReadSchema(CityTradingShopBaseSchema, TimestampMixin):
    id: uuid.UUID
    number: int

class CityTradingShopUpdateInfoSchema(BaseModel):
    name: str
    description: str | None = None

class CityTradingShopUpdatePhotoSchema(BaseModel):
    photo_id: uuid.UUID | None = None


class ShopSaleItemSchema(BaseModel):
    """Схема для товара на продаже в магазине"""
    sale_id: uuid.UUID
    inventory_item_id: uuid.UUID
    price: Decimal
    # Поля из InventoryItem
    item_slug: str
    amount: int
    expired_date: datetime | None = None
    used_count: int | None = None
    wear: int | None = None
    item_name: str
    ability_parameters: dict | None = None
    parameters: dict | None = None
    item_type: ItemType | None = None
    minimal_level: int | None = None


class CityTradingShopResponseSchema(BaseModel):
    shop: CityTradingShopReadSchema
    settings: CityTradingShopSettingsReadSchema
    photo: FileReadSchema | None = None
    sale_items: list[ShopSaleItemSchema] = []


class CityTradingShopWithSaleItemsSchema(CityTradingShopReadSchema):
    """Схема магазина с товарами на продаже"""
    sale_items: list[ShopSaleItemSchema]
    photo: FileReadSchema | None = None


class PaginatedShopsWithSaleItemsSchema(BaseModel):
    """Схема пагинированного ответа с магазинами"""
    items: list[CityTradingShopWithSaleItemsSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class CharacterRecipeBaseSchema(BaseModel):
    character_id: uuid.UUID
    item_slug: str
    quantity: int

class CharacterRecipeReadSchema(CharacterRecipeBaseSchema, TimestampMixin):
    id: uuid.UUID
    item: ItemReadSchema

class CharacterRecipeCreateSchema(BaseModel):
    item_slug: str
    quantity: int


class InventoryItemBaseSchema(BaseModel):
    character_id: uuid.UUID | None = None
    shop_id: uuid.UUID | None = None
    # 🆕 Эскроу сделок: предмет, находящийся в сделке (deal_id is not None),
    # нельзя надевать/распаковывать/использовать. Репозитории строят схему
    # из InventoryItem.__dict__, поэтому поле подхватывается автоматически
    # для всех наследников (ReadSchema, SimpleReadSchema).
    deal_id: uuid.UUID | None = None
    item_slug: str
    amount: int
    expired_date: datetime | None = None
    used_count: int | None = None
    wear: int | None = None
    item_binding_type: ItemBindingType = ItemBindingType.NONE

class InventoryItemCreateSchema(BaseModel):
    item_slug: str
    amount: int
    expired_date: datetime | None = None
    used_count: int | None = None
    wear: int | None = 0
    item_binding_type: ItemBindingType = ItemBindingType.NONE

class InventoryItemReadSchema(InventoryItemBaseSchema, TimestampMixin):
    id: uuid.UUID
    item: ItemReadSchema
    # deal_id унаследован от InventoryItemBaseSchema


class InventoryItemSimpleReadSchema(InventoryItemBaseSchema, TimestampMixin):
    id: uuid.UUID
    item_name: str
    item_type: ItemType | None = None
    minimal_level: int | None = None
    ability_parameters: dict | None = None
    parameters: dict | None = None
    price: Decimal | None = None   
    weight: int | None = None  


class InternalFurnitureItemSchema(BaseModel):
    inventory_item_id: uuid.UUID
    slug: str
    wear: int
    max_wear: int | None = None
    volume: int | None = None
    weight: int
    ability_parameters: dict | None = None
    name: str
    shop_id: uuid.UUID | None = None


class InternalFurnitureBulkRequestSchema(BaseModel):
    inventory_item_ids: list[uuid.UUID]


class InternalFurnitureWearEntrySchema(BaseModel):
    inventory_item_id: uuid.UUID
    wear_add: int = Field(gt=0)


class InternalFurnitureWearRequestSchema(BaseModel):
    entries: list[InternalFurnitureWearEntrySchema]


class InternalFurnitureWearResponseSchema(BaseModel):
    broken_ids: list[uuid.UUID]
    

class CharacterEquipmentReadSchema(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    inventory_item_id: uuid.UUID
    slot: EquipmentSlot
    model_config = ConfigDict(from_attributes=True)


class SaleInventoryItemBaseSchema(BaseModel):
    inventory_item_id: uuid.UUID
    price: Decimal

class SaleInventoryItemCreateSchema(BaseModel):
    price: Decimal = Field(gt=0, le=Decimal("9999999.99"))
    amount: int = Field(default=1, gt=0, le=9999999)

class InventoryItemAmountSchema(BaseModel):
    amount: int = Field(default=1, gt=0, le=9999999)

class SalePriceUpdateSchema(BaseModel):
    price: Decimal = Field(gt=0, le=Decimal("9999999.99"))

class SaleInventoryItemReadSchema(SaleInventoryItemBaseSchema, TimestampMixin):
    id: uuid.UUID
    item_name: str
    # Поля из InventoryItem
    character_id: uuid.UUID | None = None
    shop_id: uuid.UUID | None = None
    item_slug: str
    amount: int
    expired_date: datetime | None = None
    used_count: int | None = None
    wear: int | None = None
    ability_parameters: dict | None = None 
    parameters: dict | None = None
    item_type: ItemType | None = None
    minimal_level: int | None = None
    item_price: Decimal | None = None
    weight: int | None = None


class LocationItemsGroupedSchema(BaseModel):
    character_items: list[InventoryItemSimpleReadSchema]
    shop_items: list[InventoryItemSimpleReadSchema]
    sale_items: list[SaleInventoryItemReadSchema]
    current_capacity: int = 0   # ✅ текущий объём лавки
    max_capacity: int = 0       # ✅ макс. вместимость лавки
    shop_end_license: datetime | None = None        # для обычных лавок
    crafting_license_active: bool | None = None     # для production-локаций



class ItemExperienceForLevelBaseSchema(BaseModel):
    experience: int
    level: int
    success_rate_one: float = 0.0

class ItemExperienceForLevelCreateSchema(ItemExperienceForLevelBaseSchema, CreateBaseModel):
    pass

class ItemExperienceForLevelReadSchema(ItemExperienceForLevelBaseSchema, TimestampMixin):
    id: uuid.UUID


class CharacterCityTradeStatsBaseSchema(BaseModel):
    character_id: uuid.UUID
    location_slug: str
    experience: int = 0
    level: int = 1

class CharacterCityTradeStatsCreateSchema(BaseModel):
    character_id: uuid.UUID
    location_slug: str

class CharacterCityTradeStatsReadSchema(CharacterCityTradeStatsBaseSchema, TimestampMixin):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class ItemComponentWithResourceSchema(BaseModel):
    """Схема компонента с названием ресурса"""
    id: uuid.UUID
    item_slug: str
    resource_slug: str
    quantity: int
    resource_name: str

class ResourceItemWithComponentsReadSchema(ResourceItemReadSchema):
    """Рецепт сразу с компонентами, чтобы фронтенд не делал запросы /details"""
    components: list[ItemComponentWithResourceSchema] = []


class ItemDetailsSchema(BaseModel):
    """Схема детальной информации об Item с компонентами"""
    item: ItemReadSchema
    components: list[ItemComponentWithResourceSchema]


class CharacterRecipeWithDetailsSchema(BaseModel):
    """Схема рецепта персонажа с детальной информацией"""
    recipe_id: uuid.UUID
    quantity: int
    item_details: ItemDetailsSchema


class ItemComponentWithResourceAndStockSchema(BaseModel):
    """Схема компонента с названием ресурса и информацией о наличии"""
    id: uuid.UUID
    item_slug: str
    resource_slug: str
    quantity: int
    resource_name: str
    is_in_stock: bool


class ItemDetailsWithStockSchema(BaseModel):
    """Схема детальной информации об Item с компонентами и информацией о наличии"""
    item: ItemReadSchema
    components: list[ItemComponentWithResourceAndStockSchema]


class CharacterRecipeWithStockSchema(BaseModel):
    """Схема рецепта персонажа с информацией о наличии ресурсов"""
    id: uuid.UUID 
    recipe_id: uuid.UUID
    quantity: int | None = None
    craft_stage: int | None = None
    item_details: ItemDetailsWithStockSchema


# Building schemas
class BuildingBaseSchema(BaseModel):
    location_slug: str
    city_trading_location_slug: str

class BuildingCreateSchema(BuildingBaseSchema, CreateBaseModel):
    pass

class BuildingReadSchema(BuildingBaseSchema):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# CharacterStartCreatingItem schemas
class CharacterStartCreatingItemBaseSchema(BaseModel):
    character_id: uuid.UUID
    item_slug: str
    craft_stage: int

class CharacterStartCreatingItemCreateSchema(CreateBaseModel):
    character_id: uuid.UUID
    item_slug: str
    craft_stage: int = 0

class CharacterStartCreatingItemUpdateSchema(BaseModel):
    craft_stage: int

class CharacterStartCreatingItemReadSchema(CharacterStartCreatingItemBaseSchema, TimestampMixin):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# ItemsCreatingAction schemas
class ItemsCreatingActionBaseSchema(BaseModel):
    character_id: uuid.UUID
    location_slug: str
    start_time: datetime
    finish_time: datetime
    status: ItemCreatingStatus
    message: str
    celery_task_id: str | None = None
    result_status: ResultStatus | None = None
    recived_item_slug: str | None = None
    quantity: int | None = None
    craft_stage: int
    lost_resource: str | None = None

class ItemsCreatingActionCreateSchema(CreateBaseModel):
    character_id: uuid.UUID
    location_slug: str
    start_time: datetime
    finish_time: datetime
    status: ItemCreatingStatus
    message: str
    quantity: int | None = None
    craft_stage: int = 0

class ItemsCreatingActionUpdateSchema(UpdateBaseModel):
    character_id: uuid.UUID
    location_slug: str
    start_time: datetime
    finish_time: datetime
    status: ItemCreatingStatus
    message: str
    celery_task_id: str | None = None
    result_status: ResultStatus | None = None
    recived_item_slug: str | None = None
    quantity: int | None = None
    craft_stage: int
    lost_resource: str | None = None

class ItemsCreatingActionReadSchema(ItemsCreatingActionBaseSchema, TimestampMixin):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class ItemsCreatingActionResponseSchema(BaseModel):
    """Response schema for current crafting action status"""
    id: uuid.UUID | None = None
    status: ItemCreatingStatus
    location_slug: str | None = None
    message: str | None = None
    remaining_time_seconds: int | None = None
    finish_time: datetime | None = None


class CreateNewItemCraftingRequestSchema(BaseModel):
    """Request schema for creating new item crafting action"""
    captcha_id: str
    user_input: str


class ContinueItemCraftingRequestSchema(BaseModel):
    """Request schema for continuing item crafting action"""
    captcha_id: str
    user_input: str

class CraftingLicenseReadSchema(BaseModel):
    id: uuid.UUID | None = None
    character_id: uuid.UUID
    location_slug: str
    end_date: datetime | None = None
    is_active: bool
    number: int | None = None
    model_config = ConfigDict(from_attributes=True)

class CraftingLicenseCreateSchema(BaseModel):
    location_slug: str

class SaleHistoryReadSchema(BaseModel):
    id: uuid.UUID
    item_slug: str
    item_name: str
    amount: int
    price: Decimal
    tax: Decimal
    buyer_name: str
    location_slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)