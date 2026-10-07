import uuid
from decimal import Decimal
from fastapi import status
from typing import Optional
from shared.exceptions import CoreException

class InsufficientFundsError(CoreException):
    """
    Ошибка, возникающая при недостатке средств для выполнения операции.
    """
    def __init__(
        self,
        detail: str = "Insufficient funds to perform the operation",
        error_code: str = "INSUFFICIENT_FUNDS",
        required_amount: Optional[Decimal] = None,
        current_amount: Optional[Decimal] = None,
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

class InvalidCourseError(CoreException):
    """
    Ошибка, возникающая при неверном курсе обмена валют.
    """
    def __init__(
        self,
        detail: str = "Invalid exchange course",
        error_code: str = "INVALID_COURSE",
        min_course: Optional[int] = None,
        max_course: Optional[int] = None,
        actual_course: Optional[float] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if min_course is not None:
            extras["min_course"] = min_course
        if max_course is not None:
            extras["max_course"] = max_course
        if actual_course is not None:
            extras["actual_course"] = actual_course
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="InvalidCourseError",
            extras=extras,
            headers=headers
        )

class SlotLimitExceededError(CoreException):
    """
    Ошибка, возникающая при превышении лимитов слота.
    """
    def __init__(
        self,
        detail: str = "Slot limits exceeded",
        error_code: str = "SLOT_LIMITS_EXCEEDED",
        field: str = "amount",
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        actual_value: Optional[Decimal] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        extras["field"] = field
        if min_value is not None:
            extras["min_value"] = min_value
        if max_value is not None:
            extras["max_value"] = max_value
        if actual_value is not None:
            extras["actual_value"] = actual_value
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="SlotLimitExceededError",
            extras=extras,
            headers=headers
        )

class InvalidSlotAmountError(CoreException):
    """
    Ошибка, возникающая при неверном количестве валюты в слоте.
    """
    def __init__(
        self,
        detail: str = "Invalid slot amount",
        error_code: str = "INVALID_SLOT_AMOUNT",
        field: str = "amount",
        min_value: Optional[Decimal] = None,
        actual_value: Optional[Decimal] = None,
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        extras["field"] = field
        if min_value is not None:
            extras["min_value"] = min_value
        if actual_value is not None:
            extras["actual_value"] = actual_value
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="InvalidSlotAmountError",
            extras=extras,
            headers=headers
        )

class CharacterNotEligibleError(CoreException):
    """
    Ошибка, возникающая когда персонаж не может создать слот.
    """
    def __init__(
        self,
        detail: str = "Character is not eligible to create slot",
        error_code: str = "CHARACTER_NOT_ELIGIBLE",
        requirement: str = "unknown",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        extras["requirement"] = requirement
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CharacterNotEligibleError",
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
        provided_value: Optional[Decimal] = None,
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

class CannotTransactionWithOnlineCharacterError(CoreException):
    """
    Ошибка, возникающая при попытке открепить персонажа, который находится в онлайн состоянии.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        character_name: Optional[str] = None,
        detail: str = None,
        error_code: str = "CANNOT_TRANSACTION_ONLINE_CHARACTER",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Cannot transaction for character that is currently online"
        
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

class AmountBelowMinimumError(CoreException):
    """
    Ошибка, возникающая когда указанная сумма меньше минимально допустимой.
    """
    def __init__(
        self,
        detail: str = "Amount is below minimum allowed value",
        error_code: str = "AMOUNT_BELOW_MINIMUM",
        field: str = "amount",
        min_value: Optional[Decimal] = None,
        actual_value: Optional[Decimal] = None,
        currency: str = "",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if extras is None:
            extras = {}
        
        extras["field"] = field
        if min_value is not None:
            extras["min_value"] = min_value
        if actual_value is not None:
            extras["actual_value"] = actual_value
        if currency:
            extras["currency"] = currency
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="AmountBelowMinimumError",
            extras=extras,
            headers=headers
        )