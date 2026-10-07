import uuid
from datetime import UTC, datetime, timedelta

import httpx
import jwt

from mining_app.settings import settings
from shared.schemas.base import StatusOkSchema
from shared.schemas.captcha import CaptchaVerificationRequest
from shared.schemas.errors import BaseResponseSchema

from ....core.utils.exceptions import ExternalServiceError


class CaptchaServiceSyncClient:
    def __init__(self, base_url: str = settings.captcha_service_app.base_url, timeout: float = 15.0):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        self.token = self._generate_token()

    def _generate_token(self):
        now = datetime.now(UTC)
        payload = {
            "iss": settings.service_name,
            "aud": "captcha-service",
            "permissions": ["captcha:read", "captcha:write"],
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
                service_name="captcha-service",
                method=method,
                endpoint=path,
                detail=f"HTTP {response.status_code}: {detail}",
                error_code="EXTERNAL_SERVICE_ERROR",
                status_code=response.status_code,
            )
        if response_model:
            return response_model.model_validate(response.json())
        return None

    def verify_captcha(self, captcha: CaptchaVerificationRequest) -> StatusOkSchema:
        return self._request(
            "POST",
            "/verify",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=captcha.model_dump(mode="json")
        )

    def close(self):
        self.client.close()