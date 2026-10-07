import uuid
from decimal import Decimal
from typing import Protocol, Self

import httpx
from pydantic import BaseModel, model_validator

from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import (
    CharacterCurrencyOperationResponse,
    CharacterItemsBalance,
    CharacterMiningStats,
    CharacterReadSchema,
    CharacterWeightBalance,
    DucatsStat,
    PaginationCharacterSimpleInfoReadSchema,
    TirednessStat,
    WeightStat,
)
from shared.schemas.errors import BaseResponseSchema

from ....core.adapters.base_http import BaseHttpClientImpl


def _serialize_value(v):
    """Рекурсивная сериализация значений для JSON: Decimal, UUID, datetime → str."""
    from datetime import datetime
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _serialize_value(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_serialize_value(x) for x in v]
    return v

def _serialize_meta(meta: dict | None) -> dict | None:
    if not meta:
        return meta
    return _serialize_value(meta)

class CharacterServiceClientProtocol(Protocol):
    async def search_characters(self: Self, search: str | None, limit: int, offset: int) -> "InternalCharacterSearchResponse":
        ...

    async def get_simple_character_balance(self: Self, character_id: uuid.UUID) -> CharacterItemsBalance:
        """Получение простой информации о персонаже по ID"""
        ...

    async def get_full_character(self: Self, character_id: uuid.UUID) -> CharacterReadSchema:
        """Получение полной информации о персонаже (включая силу, ловкость, удачу)"""
        ...

    async def get_character_for_requirements(self: Self, character_id: uuid.UUID) -> "CharacterForRequirements":
        ...

    async def update_ducats(self, character_id: uuid.UUID, ducats: Decimal) -> StatusOkSchema:
        ...

    async def get_character_weight_balance(self: Self, character_id: uuid.UUID) -> CharacterWeightBalance:
        """Получение информации о весе персонажа"""
        ...

    async def get_simple_info_character(self: Self, character_id: uuid.UUID) -> CharacterMiningStats:
        """Получение простой информации о персонаже по ID"""
        ...

    async def update_weight(self, character_id: uuid.UUID, weight: float) -> StatusOkSchema:
        """Обновление веса персонажа"""
        ...

    async def update_tiredness(self, character_id: uuid.UUID, tiredness: float) -> StatusOkSchema:
        ...

    async def get_online_characters(self, location_slug: str) -> PaginationCharacterSimpleInfoReadSchema:
        ...

    async def get_trade_privileges(self, character_id: uuid.UUID) -> "CharacterTradePrivileges": 
        ...
    async def debit_gold(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID, operation_type: str, source: str, item_meta: dict, counterparty_id: uuid.UUID | None = None) -> CharacterCurrencyOperationResponse: 
        ...
    async def credit_gold(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID, operation_type: str, source: str, item_meta: dict, counterparty_id: uuid.UUID | None = None) -> CharacterCurrencyOperationResponse: 
        ...
    async def debit_ducats(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID | None = None, operation_type: str | None = None, source: str | None = None, counterparty_id: uuid.UUID | None = None, item_meta: dict | None = None, meta: dict | None = None) -> CharacterCurrencyOperationResponse:
        ...
    async def credit_ducats(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID | None = None, operation_type: str | None = None, source: str | None = None, counterparty_id: uuid.UUID | None = None, item_meta: dict | None = None, meta: dict | None = None) -> CharacterCurrencyOperationResponse:
        ...

    async def apply_buff(self: Self, character_id: uuid.UUID, buff_type: str, value: int, duration_seconds: int, source: str, source_name: str | None = None) -> StatusOkSchema: 
        ...

    async def consume_food(self: Self, character_id: uuid.UUID, effects: list[dict], cooldown_seconds: int, required_location_slug: str | None = None) -> StatusOkSchema: 
        ...

    async def recalculate_equipment_bonuses(self: Self, character_id: uuid.UUID, bonuses: dict) -> StatusOkSchema:
        """Пересчитать бонусы экипировки"""
        ...

    async def get_installed_furniture_item_ids(self: Self) -> list[uuid.UUID]:
        """Получить список inventory_item_id, установленных в домах."""
        ...


class CharacterTradePrivileges(BaseModel):
    gold_trade_enabled: bool


class InternalCharacterSearchItem(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    location_slug: str | None = None
    is_online: bool


class InternalCharacterSearchResponse(BaseModel):
    objects: list[InternalCharacterSearchItem]
    count: int

class InstalledFurnitureIdsResponse(BaseModel):
    inventory_item_ids: list[uuid.UUID] = []

class CharacterForRequirements(BaseModel):
    id: uuid.UUID
    name: str
    race: str | None = None
    level: int = 0
    power: int = 0
    agility: int = 0
    lucky: int = 0
    equipment_bonuses: dict = {}
    eff_power: int = 0
    eff_agility: int = 0
    eff_lucky: int = 0

    @model_validator(mode='before')
    @classmethod
    def unwrap_info(cls, data):
        if isinstance(data, dict) and 'info' in data and 'additional_info' in data:
            return data['info']
        return data

class CharacterServiceClient(BaseHttpClientImpl, CharacterServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        stats_base_url: str,
        timeout: float = 15.0,  
        permissions: list[str] | None = None
    ):
        if permissions is None:
            permissions = ["characters:read", "characters:write"]
        super().__init__(
            base_url=base_url,
            target_service="character-service", 
            permissions=permissions,
            timeout=timeout
        )
        self.stats_base_url = stats_base_url.rstrip("/")

    async def get_simple_info_character(self: Self, character_id: uuid.UUID) -> CharacterMiningStats:
        return await self.request(
            "GET",
            f"/simple/info/{character_id}",
            response_model=CharacterMiningStats,
            error_model=BaseResponseSchema,
        )

    async def search_characters(self: Self, search: str | None, limit: int, offset: int) -> InternalCharacterSearchResponse:
        return await self.request(
            "GET",
            "/internal/characters/search",
            response_model=InternalCharacterSearchResponse,
            error_model=BaseResponseSchema,
            params={"search": search, "limit": limit, "offset": offset},
        )

    async def get_full_character(self: Self, character_id: uuid.UUID) -> CharacterReadSchema:
        from pydantic import model_validator
        
        class UnwrappedCharacterReadSchema(CharacterReadSchema):
            @model_validator(mode='before')
            @classmethod
            def unwrap_info(cls, data):
                if isinstance(data, dict) and 'info' in data and 'additional_info' in data:
                    return data['info']
                return data
        
        return await self.request(
            "GET",
            f"/{character_id}",
            response_model=UnwrappedCharacterReadSchema,
            error_model=BaseResponseSchema,
        )
    
    async def get_character_for_requirements(self: Self, character_id: uuid.UUID) -> "CharacterForRequirements":
        """Персонаж с ИТОГОВЫМИ статами (база + экипировка + баффы) для проверки требований"""        

        # 1. База + бонусы экипировки
        char = await self.request(
            "GET",
            f"/{character_id}",
            response_model=CharacterForRequirements,
            error_model=BaseResponseSchema,
        )

        # 2. Активные баффы (другой префикс /api/stats — прямой httpx)
        buff_bonus = {"strength_bonus": 0, "agility_bonus": 0, "luck_bonus": 0}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.stats_base_url}/{character_id}/buffs")
                if resp.status_code == 200:
                    for b in (resp.json().get("buffs") or []):
                        if not b.get("is_active"):
                            continue
                        bt, v = b.get("buff_type"), b.get("value", 0) or 0
                        if bt == "strength_boost":
                            buff_bonus["strength_bonus"] += v
                        elif bt == "agility_boost":
                            buff_bonus["agility_bonus"] += v
                        elif bt == "luck_boost":
                            buff_bonus["luck_bonus"] += v
        except Exception as e:
            # Если баффы недоступны — считаем без них, не роняем применение
            print(f"[requirements] buffs fetch skipped: {e}")

        eb = char.equipment_bonuses or {}
        char.eff_power = char.power + (eb.get("strength_bonus") or 0) + buff_bonus["strength_bonus"]
        char.eff_agility = char.agility + (eb.get("agility_bonus") or 0) + buff_bonus["agility_bonus"]
        char.eff_lucky = char.lucky + (eb.get("luck_bonus") or 0) + buff_bonus["luck_bonus"]
        return char
    
    async def get_online_characters(self, location_slug: str) -> PaginationCharacterSimpleInfoReadSchema:
        return await self.request(
            "GET",
            "/online",
            response_model=PaginationCharacterSimpleInfoReadSchema,
            error_model=BaseResponseSchema,
            params={"location_slug": location_slug, "limit": 100, "offset": 0},
        )

    async def get_trade_privileges(self, character_id: uuid.UUID) -> CharacterTradePrivileges:
        return await self.request(
            "GET",
            f"/internal/characters/{character_id}/trade-privileges",
            response_model=CharacterTradePrivileges,
            error_model=BaseResponseSchema,
        )
    
    async def get_simple_character_balance(self: Self, character_id: uuid.UUID) -> CharacterItemsBalance:
        return await self.request(
            "GET",
            f"/simple/{character_id}/balance",
            response_model=CharacterItemsBalance,
            error_model=BaseResponseSchema,
        )
    
    async def update_ducats(self, character_id: uuid.UUID, ducats: Decimal) -> StatusOkSchema:
        stats = DucatsStat(ducats=ducats)
        return await self.request(
            "PUT",
            f"/{character_id}/ducats",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )
    
    async def get_character_weight_balance(self: Self, character_id: uuid.UUID) -> CharacterWeightBalance:
        return await self.request(
            "GET",
            f"/simple/{character_id}/weight",
            response_model=CharacterWeightBalance,
            error_model=BaseResponseSchema,
        )
    
    async def update_weight(self, character_id: uuid.UUID, weight: float) -> StatusOkSchema:
        stats = WeightStat(weight=weight)
        return await self.request(
            "PUT",
            f"/{character_id}/weight",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )

    async def update_tiredness(self, character_id: uuid.UUID, tiredness: float) -> StatusOkSchema:
        stats = TirednessStat(tiredness=tiredness)
        return await self.request(
            "PUT",
            f"/{character_id}/tiredness",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )

    async def debit_ducats(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        counterparty_id: uuid.UUID | None = None,
        item_meta: dict | None = None,
        meta: dict | None = None,
    ) -> CharacterCurrencyOperationResponse:
        """Списывает дукаты через internal ledger endpoint characters service."""
        payload = {
            "operation_id": str(operation_id or uuid.uuid4()),
            "amount": str(amount),
            "operation_type": operation_type,
            "source": source,
            "counterparty_id": str(counterparty_id) if counterparty_id else None,
            "item_meta": _serialize_meta(item_meta),
            "meta": _serialize_meta(meta),
        }

        return await self.request(
            "POST",
            f"/internal/characters/{character_id}/ducats/debit",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json=payload
        )

    async def credit_ducats(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        counterparty_id: uuid.UUID | None = None,
        item_meta: dict | None = None,
        meta: dict | None = None,
    ) -> CharacterCurrencyOperationResponse:
        """Зачисляет дукаты через internal ledger endpoint characters service."""
        payload = {
            "operation_id": str(operation_id or uuid.uuid4()),
            "amount": str(amount),
            "operation_type": operation_type,
            "source": source,
            "counterparty_id": str(counterparty_id) if counterparty_id else None,
            "item_meta": _serialize_meta(item_meta),
            "meta": _serialize_meta(meta),
        }

        return await self.request(
            "POST",
            f"/internal/characters/{character_id}/ducats/credit",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json=payload
        )

    async def _change_gold(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID, operation_type: str, source: str, item_meta: dict, direction: str, counterparty_id: uuid.UUID | None = None) -> CharacterCurrencyOperationResponse:
        return await self.request(
            "POST",
            f"/internal/characters/{character_id}/gold/{direction}",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json={
                "operation_id": str(operation_id),
                "amount": str(amount),
                "operation_type": operation_type,
                "source": source,
                "item_meta": _serialize_meta(item_meta),
                "counterparty_id": str(counterparty_id) if counterparty_id else None,
            },
        )

    async def debit_gold(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID, operation_type: str, source: str, item_meta: dict, counterparty_id: uuid.UUID | None = None) -> CharacterCurrencyOperationResponse:
        return await self._change_gold(character_id, amount, operation_id, operation_type, source, item_meta, "debit", counterparty_id)

    async def credit_gold(self, character_id: uuid.UUID, amount: Decimal, operation_id: uuid.UUID, operation_type: str, source: str, item_meta: dict, counterparty_id: uuid.UUID | None = None) -> CharacterCurrencyOperationResponse:
        return await self._change_gold(character_id, amount, operation_id, operation_type, source, item_meta, "credit", counterparty_id)

    async def apply_buff(
        self,
        character_id: uuid.UUID,
        buff_type: str,
        value: int,
        duration_seconds: int,
        source: str,
        source_name: str | None = None
    ) -> StatusOkSchema:
        
        # Прямой вызов на правильный URL
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.stats_base_url}/buffs/apply",
                json={
                    "character_id": str(character_id),
                    "buff_type": buff_type,
                    "value": value,
                    "duration_seconds": duration_seconds,
                    "source": source,
                    "source_name": source_name
                }
            )
            
            # Перехватываем ошибки от characters и пробрасываем как CoreException
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("extras", {}).get("message") or error_data.get("detail") or "Ошибка при применении эффекта"
                except Exception:
                    error_message = f"Ошибка {response.status_code} от characters сервиса"
                
                from shared.exceptions import CoreException
                raise CoreException(
                    status_code=response.status_code,
                    detail=error_message,
                    error_code="BUFF_APPLY_ERROR",
                    error_type="ValidationError",
                    extras={"field": "buff_type", "message": error_message}
                )
            
            return StatusOkSchema(status="ok")

    async def consume_food(
        self,
        character_id: uuid.UUID,
        effects: list[dict],
        cooldown_seconds: int,
        required_location_slug: str | None = None
    ) -> StatusOkSchema:

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.stats_base_url}/food/consume",
                json={
                    "character_id": str(character_id),
                    "effects": effects,
                    "cooldown_seconds": cooldown_seconds,
                    "required_location_slug": required_location_slug,
                }
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("extras", {}).get("message") or error_data.get("detail") or "Ошибка при применении еды"
                except Exception:
                    error_message = f"Ошибка {response.status_code} от characters сервиса"

                from shared.exceptions import CoreException
                raise CoreException(
                    status_code=response.status_code,
                    detail=error_message,
                    error_code="FOOD_CONSUME_ERROR",
                    error_type="ValidationError",
                    extras={"field": "food_cooldown", "message": error_message}
                )

            return StatusOkSchema(status="ok")
        

    async def recalculate_equipment_bonuses(
        self,
        character_id: uuid.UUID,
        bonuses: dict
    ) -> StatusOkSchema:
        """
        Отправляет запрос на пересчёт бонусов экипировки в Characters сервис.
        
        Args:
            character_id: ID персонажа
            bonuses: Суммарные бонусы {"strength_bonus": 5, ...}
        
        Returns:
            StatusOkSchema
        
        Raises:
            HTTPError: Если запрос упал
        """
        return await self.request(
            "POST",
            f"/internal/characters/{character_id}/equipment/recalculate",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json={"bonuses": bonuses}
        )
    

    async def get_installed_furniture_item_ids(self: Self) -> list[uuid.UUID]:
        response = await self.request(
            "GET",
            "/internal/houses/furniture/inventory-item-ids",
            response_model=InstalledFurnitureIdsResponse,
            error_model=BaseResponseSchema,
        )
        return response.inventory_item_ids
