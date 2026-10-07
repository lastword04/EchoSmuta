from typing import Any
from ...core.utils.exceptions import ModelFieldNotFoundException
from .models import PasswordResetTokens


class TokenNotFoundError(ModelFieldNotFoundException):
    """
    Исключение, возникающее при отсутствии токена в запросе.
    """
    def __init__(
       self,
        value: Any,
        headers: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            model=PasswordResetTokens,
            field="token",
            value=value,
            headers=headers,
        )