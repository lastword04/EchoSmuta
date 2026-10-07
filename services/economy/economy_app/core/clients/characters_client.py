import uuid
import datetime
from decimal import Decimal
from typing import Any

import httpx
import jwt
from fastapi import HTTPException


class CharactersClient:
    def __init__(
        self, 
        base_url: str, 
        secret_key: str, 
        algorithm: str, 
        expire_minutes: int, 
        timeout: float = 10.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
        self.timeout = timeout

    def _generate_service_token(self) -> str:
        """Генерирует свежий JWT токен для каждого запроса"""
        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "sub": "economy-service",
            "service": "economy",
            "iat": int(now.timestamp()),
            "exp": int((now + datetime.timedelta(minutes=self.expire_minutes)).timestamp())
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _headers(self) -> dict[str, str]:
        # Токен генерируется на лету, он никогда не протухнет
        return {"Authorization": f"Bearer {self._generate_service_token()}"}

    async def get_balance(self, character_id: uuid.UUID) -> Decimal:
        url = f"{self.base_url}/api/characters/internal/characters/{character_id}/ducats"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        return Decimal(str(response.json()["ducats"]))

    async def debit(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        counterparty_id: uuid.UUID | None = None,
        item_meta: dict | None = None,
        meta: dict | None = None,
    ) -> dict[str, Any]:
        return await self._change_balance(
            "debit",
            character_id,
            amount,
            operation_id=operation_id,
            operation_type=operation_type,
            source=source,
            counterparty_id=counterparty_id,
            item_meta=item_meta,
            meta=meta,
        )

    async def credit(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        counterparty_id: uuid.UUID | None = None,
        item_meta: dict | None = None,
        meta: dict | None = None,
    ) -> dict[str, Any]:
        return await self._change_balance(
            "credit",
            character_id,
            amount,
            operation_id=operation_id,
            operation_type=operation_type,
            source=source,
            counterparty_id=counterparty_id,
            item_meta=item_meta,
            meta=meta,
        )

    async def _change_balance(
        self,
        operation: str,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        counterparty_id: uuid.UUID | None = None,
        item_meta: dict | None = None,
        meta: dict | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/api/characters/internal/characters/{character_id}/ducats/{operation}"
        payload = {
            "operation_id": str(operation_id or uuid.uuid4()),
            "amount": str(amount),
            "operation_type": operation_type,
            "source": source,
            "counterparty_id": str(counterparty_id) if counterparty_id else None,
            "item_meta": item_meta,
            "meta": meta,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def get_character_location(self, character_id: uuid.UUID) -> str:
        """Получить location_slug персонажа"""
        url = f"{self.base_url}/api/characters/simple/info/{character_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        return data["location_slug"]

    async def get_character_name(self, character_id: uuid.UUID) -> str:
        """Получить имя персонажа"""
        url = f"{self.base_url}/api/characters/simple/info/{character_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        return data["name"]

    async def consume_food(
        self,
        character_id: uuid.UUID,
        effects: list[dict],
        cooldown_seconds: int,
        required_location_slug: str | None = None,
    ):
        
        token = self._generate_service_token()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/stats/food/consume",
                json={
                    "character_id": str(character_id),
                    "effects": effects,
                    "cooldown_seconds": cooldown_seconds,
                    "required_location_slug": required_location_slug,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("extras", {}).get("message") or error_data.get("detail") or "Ошибка при применении еды"
            except Exception:
                message = f"Ошибка {response.status_code} от characters сервиса"
            raise HTTPException(status_code=response.status_code, detail=message)