import uuid
from fastapi import status
from typing import Optional
from shared.exceptions import CoreException

class CharacterLimitExceededError(CoreException):
    """
    Ошибка, возникающая при превышении лимита персонажей пользователя.
    """
    def __init__(
        self,
        limit: int,
        detail: str = None,
        error_code: str = "CHARACTER_LIMIT_EXCEEDED",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = f"User has reached the limit of {limit} characters"
        
        if extras is None:
            extras = {"limit": limit}
        else:
            extras["limit"] = limit
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CharacterLimitExceededError",
            extras=extras,
            headers=headers
        )

class InsufficientFundsError(CoreException):
    """
    Ошибка, возникающая при недостатке средств для выполнения операции.
    """
    def __init__(
        self,
        detail: str = "Insufficient funds to perform the operation",
        error_code: str = "INSUFFICIENT_FUNDS",
        required_amount: Optional[int] = None,
        current_amount: Optional[int] = None,
        currency: str = "ducats",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_amount is not None:
            extras["required_amount"] = required_amount
        if current_amount is not None:
            extras["current_amount"] = current_amount
        extras["currency"] = currency
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientFundsError",
            extras=extras,
            headers=headers
        )

class InsufficientLevelError(CoreException):
    """
    Ошибка, возникающая при недостатке уровня для выполнения операции.
    """
    def __init__(
        self,
        detail: str = "Insufficient level to perform the operation",
        error_code: str = "INSUFFICIENT_LEVEL",
        required_amount: Optional[int] = None,
        current_amount: Optional[int] = None,
        currency: str = "level",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_amount is not None:
            extras["required_amount"] = required_amount
        if current_amount is not None:
            extras["current_amount"] = current_amount
        extras["currency"] = currency
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientLevelError",
            extras=extras,
            headers=headers
        )

class CannotDetachOnlineCharacterError(CoreException):
    """
    Ошибка, возникающая при попытке открепить персонажа, который находится в онлайн состоянии.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        character_name: Optional[str] = None,
        detail: str = None,
        error_code: str = "CANNOT_UNPIN_ONLINE_CHARACTER",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Cannot unpin character that is currently online"
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        if character_name is not None:
            extras["character_name"] = character_name
            
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
            error_type="CannotUnpinOnlineCharacterError",
            extras=extras,
            headers=headers
        )

class CurrencyValidationError(CoreException):
    """
    Ошибка, возникающая при валидации валютных значений (золото, дукаты).
    """
    def __init__(
        self,
        detail: str = "Invalid currency format or value",
        error_code: str = "CURRENCY_VALIDATION_ERROR",
        field_name: Optional[str] = None,
        provided_value: Optional[float] = None,
        max_decimal_places: Optional[int] = None,
        currency_type: Optional[str] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if field_name is not None:
            extras["field_name"] = field_name
        if provided_value is not None:
            extras["provided_value"] = provided_value
        if max_decimal_places is not None:
            extras["max_decimal_places"] = max_decimal_places
        if currency_type is not None:
            extras["currency_type"] = currency_type
            
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            error_type="CurrencyValidationError",
            extras=extras,
            headers=headers
        )


class EmptyTransferError(CoreException):
    """
    Ошибка, возникающая при попытке трансфера без указания валютных сумм.
    """
    def __init__(
        self,
        detail: str = "Необходимо указать сумму для перевода хотя бы в одной валюте",
        error_code: str = "EMPTY_TRANSFER", # Или "INVALID_AMOUNT" для единообразия с фронтом
        offered_gold: Optional[float] = None,
        offered_ducats: Optional[float] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        # Добавляем информацию о полях для фронтенда
        extras["field"] = "amount" # Или можно указать оба поля, если фронтенд так обрабатывает
        
        if offered_gold is not None:
            extras["offered_gold"] = offered_gold
        if offered_ducats is not None:
            extras["offered_ducats"] = offered_ducats
            
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            error_type="EmptyTransferError",
            extras=extras,
            headers=headers
        )

class InvalidAmountError(CoreException):
    """
    Ошибка, возникающая при вводе некорректной суммы (например, отрицательное значение или не число,
    если это не отлавливается на уровне схемы).
    """
    def __init__(
        self,
        detail: str = "Введена некорректная сумма",
        error_code: str = "INVALID_AMOUNT",
        field: Optional[str] = None, # 'ducats' или 'gold'
        provided_value: Optional[float] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if field is not None:
            extras["field"] = field
        if provided_value is not None:
            extras["provided_value"] = provided_value
            
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            error_type="InvalidAmountError",
            extras=extras,
            headers=headers
        )

class MaxSkillsExceededError(CoreException):
    """
    Ошибка, возникающая при попытке увеличить количество скиллов сверх максимально возможного для персонажа.
    """
    def __init__(
        self,
        detail: str = "Cannot increase number of skills - exceeds maximum allowed for character",
        error_code: str = "MAX_SKILLS_EXCEEDED",
        requested_skills: Optional[int] = None,
        max_allowed_skills: Optional[int] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if requested_skills is not None:
            extras["requested_skills"] = requested_skills
        if max_allowed_skills is not None:
            extras["max_allowed_skills"] = max_allowed_skills
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="MaxSkillsExceededError",
            extras=extras,
            headers=headers
        )