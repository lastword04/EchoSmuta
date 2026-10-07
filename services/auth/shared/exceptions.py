from fastapi import status, HTTPException
from typing import Any, Dict, Optional
from decimal import Decimal
import uuid

class CoreException(HTTPException):
    """
    Расширенный базовый класс для всех исключений приложения.
    Предоставляет структурированные ошибки с кодом, типом и дополнительными данными.
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        error_type: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        :param status_code: HTTP статус код
        :param detail: Человекочитаемое описание ошибки
        :param error_code: Уникальный код ошибки для программной обработки
        :param error_type: Тип ошибки (опционально, определяется автоматически)
        :param extras: Дополнительные данные об ошибке
        :param headers: HTTP заголовки
        """
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )
        self.error_code = error_code
        self.error_type = error_type or self.__class__.__name__
        self.extras = extras or {}
    
    def to_dict(self) -> dict:
        """Возвращает структурированное представление ошибки"""
        # Конвертируем UUID в строки для JSON сериализации
        extras_serializable = {}
        if self.extras:
            for key, value in self.extras.items():
                if isinstance(value, uuid.UUID):
                    extras_serializable[key] = str(value)
                elif isinstance(value, Decimal):
                    extras_serializable[key] = float(value)
                else:
                    extras_serializable[key] = value
        
        return {
            "detail": self.detail,
            "error_code": self.error_code,
            "error_type": self.error_type,
            **({"extras": extras_serializable} if extras_serializable else {})
        }
    
    def __str__(self) -> str:
        """Улучшенное строковое представление для логирования"""
        extras_str = f", extras={self.extras}" if self.extras else ""
        return (
            f"{self.error_type}[{self.error_code}] (HTTP {self.status_code}): "
            f"{self.detail}{extras_str}"
        )


class InvalidTokenError(CoreException):
    """
    Исключение, возникающее при недействительном или истекшем токене.
    """
    def __init__(
        self,
        detail: str = "Invalid or expired token",
        error_code: str = "INVALID_TOKEN",
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            error_type="InvalidTokenError",
            extras=extras,
            headers=headers
        )

class PermissionDeniedError(CoreException):
    """
    Ошибка, возникающая при недостатке прав для выполнения действия.
    """
    def __init__(
        self,
        detail: str = 'Insufficient rights to perform the action',
        error_code: str = "PERMISSION_DENIED",
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="PermissionDeniedError",
            extras=extras,
            headers=headers
        )

class CharacterIsNotOnlineError(CoreException):
    """
    Ошибка, возникающая при попытке взаимодействия с персонажем, который не в сети.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        detail: str = None,
        error_code: str = "CHARACTER_NOT_ONLINE",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            if character_id is not None:
                detail = f"Character '{character_id}' is not online"
            else:
                detail = "Character is not online"
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CharacterIsNotOnlineError",
            extras=extras,
            headers=headers
        )