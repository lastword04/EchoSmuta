import uuid
from datetime import UTC, datetime, timedelta

import httpx
import jwt

from mining_app.settings import settings
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import CharacterMiningStats, TirednessStat
from shared.schemas.errors import BaseResponseSchema

from ....core.utils.exceptions import ExternalServiceError


class CharacterServiceSyncClient:
    def __init__(self, base_url: str = settings.character_service_app.base_url, timeout: float = 15.0):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        self.token = self._generate_token()

    def _generate_token(self):
        now = datetime.now(UTC)
        payload = {
            "iss": settings.service_name,
            "aud": "character-service",
            "permissions": ["characters:read", "characters:write"],
            "exp": now + timedelta(minutes=15),
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, settings.service_jwt.secret_key, algorithm=settings.service_jwt.algorithm)

    def _request(self, method: str, path: str, response_model=None, error_model=BaseResponseSchema, **kwargs):
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        response = self.client.request(method, url, headers=headers, **kwargs)
        if response.status_code >= 400:
            try:
                error = error_model.model_validate(response.json())
                detail = error.detail
            except Exception:
                detail = response.text
            raise ExternalServiceError(
                service_name="character-service",
                method=method,
                endpoint=path,
                detail=f"HTTP {response.status_code}: {detail}",
                error_code="EXTERNAL_SERVICE_ERROR",
                status_code=response.status_code,
            )
        if response_model:
            return response_model.model_validate(response.json())
        return None

    def get_simple_info_character(self, character_id: uuid.UUID) -> CharacterMiningStats:
        return self._request(
            "GET",
            f"/simple/info/{character_id}",
            response_model=CharacterMiningStats
        )

    def update_tiredness(self, character_id: uuid.UUID, tiredness: float) -> StatusOkSchema:
        stats = TirednessStat(tiredness=tiredness)
        return self._request(
            "PUT",
            f"/{character_id}/tiredness",
            response_model=StatusOkSchema,
            json=stats.model_dump(mode="json")
        )

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()