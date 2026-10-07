import uuid
import datetime
from typing import Any

import httpx
import jwt


class MiningClient:
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

    async def debit(self, resource_slug: str, character_id: uuid.UUID, amount: int, operation_id: uuid.UUID) -> dict[str, Any]:
        return await self._change_resource("debit", resource_slug, character_id, amount, operation_id)

    async def credit(self, resource_slug: str, character_id: uuid.UUID, amount: int, operation_id: uuid.UUID) -> dict[str, Any]:
        return await self._change_resource("credit", resource_slug, character_id, amount, operation_id)

    async def _change_resource(self, operation: str, resource_slug: str, character_id: uuid.UUID, amount: int, operation_id: uuid.UUID) -> dict[str, Any]:
        url = f"{self.base_url}/internal/resources/{resource_slug}/characters/{character_id}/{operation}"
        payload = {"amount": amount, "operation_id": str(operation_id)}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def get_player_resources(self, character_id: uuid.UUID) -> dict[str, Any]:
        url = f"{self.base_url}/internal/resources/characters/{character_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def get_trade_license(self, character_id: uuid.UUID) -> dict[str, Any]:
        url = f"{self.base_url}/api/items/internal/trade-licenses/{character_id}/active"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def get_locations(self) -> dict[str, Any]:
        url = f"{self.base_url}/internal/resources/locations"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def get_players_resources(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/internal/resources/players"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        return data.get("resources", [])

    async def get_all_resources(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/internal/resources/"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
