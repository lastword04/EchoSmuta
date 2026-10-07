from fastapi import status
from typing import Any
from ...core.utils.exceptions import CoreException


class InvalidTokenError(CoreException):
    """
    Исключение, возникающее при недействительном или истекшем токене.
    """

    def __init__(
        self,
        detail: str = "Invalid or expired token",
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=headers
        )
