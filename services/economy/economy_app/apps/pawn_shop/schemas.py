import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import LotStatus, LotType, ResourceCategory


class ResourceRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    icon_url: str | None
    player_quantity: int = 0   
    buyout_stock_quantity: int = 0
    sell_price: Decimal          # цена продажи (игрок платит)
    buy_price: Decimal  
    next_recalculation_at: datetime | None
    category: ResourceCategory


class TradeRequest(BaseModel):
    resource_id: uuid.UUID
    quantity: int = Field(gt=0, le=9999999)


class LotItemRequest(BaseModel):
    resource_id: uuid.UUID
    quantity: int = Field(gt=0, le=9999999)


class LotCreateRequest(BaseModel):
    lot_type: LotType
    price: Decimal = Field(gt=0, le=Decimal("9999999.99"))
    items: list[LotItemRequest] = Field(min_length=1, max_length=5)  # ← от 1 до 5 позиций
    
    @field_validator('items')
    @classmethod
    def validate_unique_resources(cls, items: list[LotItemRequest]) -> list[LotItemRequest]:
        resource_ids = [item.resource_id for item in items]
        if len(resource_ids) != len(set(resource_ids)):
            raise ValueError('Duplicate resources in lot items')
        return items


class LotItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_id: uuid.UUID
    quantity: int


class LotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_character_id: uuid.UUID
    lot_type: LotType
    status: LotStatus
    price: Decimal
    items: list[LotItemRead] = []
    created_at: datetime

class DealRequest(BaseModel):
    quantity: int = Field(gt=0, le=9999999)

class BulkTradeItem(BaseModel):
    resource_id: uuid.UUID
    quantity: int = Field(gt=0, le=9999999)

class BulkTradeRequest(BaseModel):
    items: list[BulkTradeItem] = Field(min_length=1, max_length=50)
