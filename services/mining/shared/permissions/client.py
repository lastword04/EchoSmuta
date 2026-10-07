import uuid
import httpx
from typing import Protocol
from typing_extensions import Self


class UsersInternalClientProtocol(Protocol):
    async def get_user_permissions(self: Self, user_id: uuid.UUID) -> list[str]: ...


class UsersInternalClient(UsersInternalClientProtocol):
    def __init__(self: Self, base_url: str, service_token: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token
        self.timeout = timeout

    async def get_user_permissions(self: Self, user_id: uuid.UUID) -> list[str]:
        url = f"{self.base_url}/api/users/internal/users/{user_id}/permissions"
        headers = {"Authorization": f"Bearer {self.service_token}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("permissions", [])
