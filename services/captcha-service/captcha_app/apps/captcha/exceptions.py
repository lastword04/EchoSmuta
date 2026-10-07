from fastapi import status
from typing import Any, Dict, Optional
from shared.exceptions import CoreException

class CaptchaExpiredError(CoreException):
    """Исключение, возникающее при истечении срока действия капчи."""
    def __init__(
        self,
        status_code: int = status.HTTP_410_GONE,
        detail: str = "Captcha has expired",
        error_code: str = "CAPTCHA_EXPIRED",
        error_type: str = "CaptchaExpiredError",
        extras: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code=error_code,
            error_type=error_type,
            extras=extras,
            headers=headers
        )

class InvalidCaptchaInputError(CoreException):
    """Исключение, возникающее при неверном вводе капчи пользователем."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "Invalid captcha input",
        error_code: str = "INVALID_CAPTCHA_INPUT",
        error_type: str = "InvalidCaptchaInputError",
        extras: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code=error_code,
            error_type=error_type,
            extras=extras,
            headers=headers
        )