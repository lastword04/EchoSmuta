import uuid
from fastapi import status
from typing import Optional
from shared.exceptions import CoreException

class CannotIgnoreSelfError(CoreException):
    """
    Ошибка, возникающая при попытке добавить самого себя в список игнорируемых.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        character_name: Optional[str] = None,
        detail: str = None,
        error_code: str = "CANNOT_IGNORE_SELF",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Cannot ignore yourself"
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        if character_name is not None:
            extras["character_name"] = character_name
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="CannotIgnoreSelfError",
            extras=extras,
            headers=headers
        )

class IgnoreCooldownError(CoreException):
    """
    Ошибка, возникающая при попытке игнорировать персонажа до истечения времени кулдауна.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        cooldown: float = 60.0,
        remaining_time: float = 0.0,
        detail: str = None,
        error_code: str = "IGNORE_COOLDOWN_ERROR",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = f"Character is on ignore cooldown. Try again in {remaining_time:.2f} seconds."
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        
        extras["cooldown"] = cooldown
        extras["remaining_time"] = remaining_time
            
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
            error_type="IgnoreCooldownError",
            extras=extras,
            headers=headers
        )

class ChatRateLimitExceededError(CoreException):
    """
    Ошибка, возникающая при превышении лимита отправки сообщений.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        detail: str = None,
        error_code: str = "RATE_LIMIT_EXCEEDED",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Rate limit exceeded. Please wait 1 second between messages."
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
            
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
            error_type="ChatRateLimitExceededError",
            extras=extras,
            headers=headers
        )

class ChatInvalidJSONError(CoreException):
    """
    Ошибка, возникающая при невалидном JSON в сообщении.
    """
    def __init__(
        self,
        detail: str = None,
        error_code: str = "INVALID_JSON",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Invalid JSON format"
        
        if extras is None:
            extras = {}
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="ChatInvalidJSONError",
            extras=extras,
            headers=headers
        )

class ChatDisabledError(CoreException):
    """
    Ошибка, возникающая когда чат отключен в настройках и пользователь пытается отправить сообщение.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        detail: str = None,
        error_code: str = "CHAT_DISABLED",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Chat is disabled. You cannot send messages in this chat."

        if extras is None:
            extras = {}

        if character_id is not None:
            extras["character_id"] = str(character_id)

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="ChatDisabledError",
            extras=extras,
            headers=headers
        )

class ChatValidationError(CoreException):
    """
    Ошибка, возникающая при невалидных данных сообщения.
    """
    def __init__(
        self,
        errors: list = None,
        detail: str = None,
        error_code: str = "VALIDATION_ERROR",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Validation failed"
        
        if extras is None:
            extras = {}
        
        if errors is not None:
            extras["errors"] = errors
            
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            error_type="ChatValidationError",
            extras=extras,
            headers=headers
        )

class ChatAuthError(CoreException):
    """
    Ошибка, возникающая при проблемах с аутентификацией/авторизацией.
    """
    def __init__(
        self,
        detail: str = None,
        error_code: str = "AUTH_ERROR",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Invalid token or access denied"
        
        if extras is None:
            extras = {}
            
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            error_type="ChatAuthError",
            extras=extras,
            headers=headers
        )