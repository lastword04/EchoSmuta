import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from ..pawn_shop.models import TransactionType

class AdminResourceRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    category: str 
    base_sell_price: Decimal
    base_buy_price: Decimal
    min_sell_price: Decimal
    max_sell_price: Decimal
    min_buy_price: Decimal
    max_buy_price: Decimal
    sell_price: Decimal | None
    buy_price: Decimal | None
    stock_quantity: int = 0
    next_recalculation_at: datetime | None

class AdminStockRequest(BaseModel):
    quantity: int = Field(ge=0, le=9999999)
    base_sell_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))
    base_buy_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))

class AdminSetPriceRequest(BaseModel):
    sell_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))
    buy_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))



class AdminUpdateResourceRequest(BaseModel):
    name: str | None = None
    icon_url: str | None = None
    base_sell_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))
    base_buy_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))
    min_sell_price: Decimal | None = Field(default=None, ge=0, le=Decimal("9999999.99"))
    max_sell_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))
    min_buy_price: Decimal | None = Field(default=None, ge=0, le=Decimal("9999999.99"))
    max_buy_price: Decimal | None = Field(default=None, gt=0, le=Decimal("9999999.99"))
    is_tradeable: bool | None = None


class AdminForceRecalculationRequest(BaseModel):
    force: bool = True

class AdminTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_type: TransactionType
    resource_id: uuid.UUID | None
    quantity: int
    price_per_unit: Decimal
    total: Decimal
    buyer_id: uuid.UUID | None
    seller_id: uuid.UUID | None
    lot_id: uuid.UUID | None
    created_at: datetime