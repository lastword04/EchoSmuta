import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import jwt

from mining_app.settings import settings
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import (
    CharacterCurrencyOperationResponse,
    CharacterItemsBalance,
    CharacterMiningStats,
    CharacterReadSchema,
    CharacterWeightBalance,
    DucatsStat,
    TirednessStat,
    WeightStat,
)
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
            response_model=CharacterMiningStats,
            error_model=BaseResponseSchema,
        )

    def get_full_character(self, character_id: uuid.UUID) -> CharacterReadSchema:
        return self._request(
            "GET",
            f"/{character_id}",
            response_model=CharacterReadSchema,
            error_model=BaseResponseSchema,
        )

    def update_tiredness(self, character_id: uuid.UUID, tiredness: float) -> StatusOkSchema:
        stats = TirednessStat(tiredness=tiredness)
        return self._request(
            "PUT",
            f"/{character_id}/tiredness",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )

    def get_simple_character_balance(self, character_id: uuid.UUID) -> CharacterItemsBalance:
        return self._request(
            "GET",
            f"/simple/{character_id}/balance",
            response_model=CharacterItemsBalance,
            error_model=BaseResponseSchema,
        )

    def get_character_weight_balance(self, character_id: uuid.UUID) -> CharacterWeightBalance:
        return self._request(
            "GET",
            f"/simple/{character_id}/weight",
            response_model=CharacterWeightBalance,
            error_model=BaseResponseSchema,
        )

    def update_ducats(self, character_id: uuid.UUID, ducats: Decimal) -> StatusOkSchema:
        stats = DucatsStat(ducats=ducats)
        return self._request(
            "PUT",
            f"/{character_id}/ducats",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )

    def update_weight(self, character_id: uuid.UUID, weight: float) -> StatusOkSchema:
        stats = WeightStat(weight=weight)
        return self._request(
            "PUT",
            f"/{character_id}/weight",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=stats.model_dump(mode="json")
        )

    def credit_ducats(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        item_meta: dict | None = None,
        counterparty_id: uuid.UUID | None = None,
        meta: dict | None = None,
    ) -> CharacterCurrencyOperationResponse:
        payload = {
            "operation_id": str(operation_id or uuid.uuid4()),
            "amount": str(amount),
            "operation_type": operation_type,
            "source": source,
            "counterparty_id": str(counterparty_id) if counterparty_id else None,
            "item_meta": item_meta,
            "meta": meta,
        }
        return self._request(
            "POST",
            f"/internal/characters/{character_id}/ducats/credit",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json=payload
        )

    def debit_ducats(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID | None = None,
        operation_type: str | None = None,
        source: str | None = None,
        item_meta: dict | None = None,
        counterparty_id: uuid.UUID | None = None,
        meta: dict | None = None,
    ) -> CharacterCurrencyOperationResponse:
        payload = {
            "operation_id": str(operation_id or uuid.uuid4()),
            "amount": str(amount),
            "operation_type": operation_type,
            "source": source,
            "counterparty_id": str(counterparty_id) if counterparty_id else None,
            "item_meta": item_meta,
            "meta": meta,
        }
        return self._request(
            "POST",
            f"/internal/characters/{character_id}/ducats/debit",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json=payload
        )

    def debit_gold(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID,
        operation_type: str,
        source: str,
        item_meta: dict,
        counterparty_id: uuid.UUID | None = None,
    ) -> CharacterCurrencyOperationResponse:
        return self._request(
            "POST",
            f"/internal/characters/{character_id}/gold/debit",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json={
                "operation_id": str(operation_id),
                "amount": str(amount),
                "operation_type": operation_type,
                "source": source,
                "item_meta": item_meta,
                "counterparty_id": str(counterparty_id) if counterparty_id else None,
            },
        )

    def credit_gold(
        self,
        character_id: uuid.UUID,
        amount: Decimal,
        operation_id: uuid.UUID,
        operation_type: str,
        source: str,
        item_meta: dict,
        counterparty_id: uuid.UUID | None = None,
    ) -> CharacterCurrencyOperationResponse:
        return self._request(
            "POST",
            f"/internal/characters/{character_id}/gold/credit",
            response_model=CharacterCurrencyOperationResponse,
            error_model=BaseResponseSchema,
            json={
                "operation_id": str(operation_id),
                "amount": str(amount),
                "operation_type": operation_type,
                "source": source,
                "item_meta": item_meta,
                "counterparty_id": str(counterparty_id) if counterparty_id else None,
            },
        )

    def close(self):
        self.client.close()