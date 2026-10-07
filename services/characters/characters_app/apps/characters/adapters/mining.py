import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from ....core.adapters.base_http import BaseHttpClientImpl
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, RootModel


class TradeLicenseActiveSchema(BaseModel):
    character_id: uuid.UUID
    active: bool
    end_date: datetime | None = None
    deal_tax_rate: Decimal | None = None
    exchange_tax_rate: Decimal | None = None


class MiningFurnitureItemSchema(BaseModel):
    inventory_item_id: uuid.UUID
    slug: str
    wear: int
    max_wear: int | None = None
    volume: int | None = None
    weight: int
    ability_parameters: dict | None = None
    name: str
    shop_id: uuid.UUID | None = None


class MiningFurnitureListSchema(RootModel[list[MiningFurnitureItemSchema]]):
    pass


class MiningFurnitureBulkRequestSchema(BaseModel):
    inventory_item_ids: list[uuid.UUID]


class MiningFurnitureWearEntrySchema(BaseModel):
    inventory_item_id: uuid.UUID
    wear_add: int


class MiningFurnitureWearRequestSchema(BaseModel):
    entries: list[MiningFurnitureWearEntrySchema]


class MiningFurnitureWearResponseSchema(BaseModel):
    broken_ids: list[uuid.UUID]


class MiningServiceClientProtocol(Protocol):
    async def get_equipment_bonuses(self: Self, character_id: uuid.UUID) -> dict:
        """
        Получает суммарные бонусы экипировки персонажа из Mining сервиса.
        
        Используется для recovery механизма при входе в игру.
        
        Returns:
            dict: Суммарные бонусы {"strength_bonus": 5, ...}
        """
        ...

    async def has_active_trade_license(self: Self, character_id: uuid.UUID) -> bool:
        """
        Возвращает True, если у персонажа активна лицензия торговца.
        """
        ...

    async def get_character_furniture(
        self: Self,
        character_id: uuid.UUID
    ) -> list[MiningFurnitureItemSchema]:
        """
        Возвращает список мебели персонажа из mining-сервиса.
        """
        ...

    async def get_furniture_bulk(
        self: Self,
        inventory_item_ids: list[uuid.UUID],
    ) -> list[MiningFurnitureItemSchema]:
        """
        Читает мебель пачкой по списку inventory_item_id.
        Используется Celery-задачей износа.
        """
        ...

    async def add_furniture_wear_bulk(
        self: Self,
        entries: list[tuple[uuid.UUID, int]],
    ) -> list[uuid.UUID]:
        """
        Инкремент wear пачкой с капом по max_wear.
        Возвращает id предметов, которые достигли max_wear этим вызовом.
        """
        ...


class MiningServiceClient(BaseHttpClientImpl, MiningServiceClientProtocol):
    def __init__(
        self,
        base_url: str,
        timeout: float = 15.0,
        permissions: list[str] = ["mining:read"]
    ):
        super().__init__(
            base_url=base_url,
            target_service="mining-service",
            permissions=permissions,
            timeout=timeout
        )

    async def get_equipment_bonuses(self, character_id: uuid.UUID) -> dict:
        """
        Получает суммарные бонусы экипировки персонажа из Mining сервиса.
        
        Используется для recovery механизма при входе в игру.
        
        Args:
            character_id: ID персонажа
            
        Returns:
            dict: Суммарные бонусы {"strength_bonus": 5, ...}
        
        Raises:
            httpx.HTTPError: Если запрос упал
        """
        response = await self.request(
            "GET",
            f"/internal/equipment/{character_id}/bonuses",
            response_model=dict,
            error_model=BaseResponseSchema,
        )
        
        # API возвращает {"bonuses": {...}}, нужно извлечь bonuses
        if isinstance(response, dict) and "bonuses" in response:
            return response["bonuses"]
        return response

    async def has_active_trade_license(self, character_id: uuid.UUID) -> bool:
        print(f"🔍 [adapter] has_active_trade_license called for {character_id}")
        try:
            response = await self.request(
                "GET",
                f"/internal/trade-licenses/{character_id}/active",
                response_model=TradeLicenseActiveSchema,                
                error_model=BaseResponseSchema,
            )
            print(f"🔍 [adapter] response={response}")
            if isinstance(response, dict):
                return bool(response.get("active", False))
            return bool(getattr(response, "active", False))
        except Exception as e:
            print(f"🔍 [adapter] EXCEPTION: {type(e).__name__}: {e}")
            return False

    async def get_character_furniture(
        self,
        character_id: uuid.UUID
    ) -> list[MiningFurnitureItemSchema]:
        response = await self.request(
            "GET",
            f"/internal/inventory/{character_id}/furniture",
            response_model=MiningFurnitureListSchema,
            error_model=BaseResponseSchema,
        )
        return response.root

    
    async def get_furniture_bulk(
        self,
        inventory_item_ids: list[uuid.UUID],
    ) -> list[MiningFurnitureItemSchema]:
        if not inventory_item_ids:
            return []
        response = await self.request(
            "POST",
            "/internal/inventory/furniture/bulk",
            json={"inventory_item_ids": [str(i) for i in inventory_item_ids]},
            response_model=MiningFurnitureListSchema,
            error_model=BaseResponseSchema,
        )
        return response.root

    async def add_furniture_wear_bulk(
        self,
        entries: list[tuple[uuid.UUID, int]],
    ) -> list[uuid.UUID]:
        if not entries:
            return []
        response = await self.request(
            "POST",
            "/internal/inventory/furniture/wear",
            json={"entries": [{"inventory_item_id": str(i), "wear_add": n} for i, n in entries]},
            response_model=MiningFurnitureWearResponseSchema,
            error_model=BaseResponseSchema,
        )
        return response.broken_ids
