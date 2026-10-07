import uuid
from fastapi import status
from typing import Any, Generic, TypeVar, Dict
from shared.exceptions import CoreException
from ..db import Base

ModelType = TypeVar('ModelType', bound=Base)


class ModelNotFoundException(CoreException, Generic[ModelType]):
    """
    Исключение не найденной модели.
    """
    def __init__(
        self,
        model: type[ModelType],
        model_id: uuid.UUID | None = None,
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        detail = (
            f'Unable to find the {model.__name__} with id {model_id}.'
            if model_id is not None
            else f'{model.__name__} id not found.'
        )
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        if model_id is not None:
            extras_data["id"] = str(model_id)
        extras_data["resource"] = model.__name__
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="MODEL_NOT_FOUND",
            error_type="ModelNotFoundException",
            extras=extras_data,
            headers=headers
        )
        self.model = model
        self.model_id = model_id


class ModelFieldNotFoundException(CoreException, Generic[ModelType]):
    """
    Исключение, возникающее при отсутствии модели с указанным значением поля.
    """
    def __init__(
        self,
        model: type[ModelType],
        field: str,
        value: Any,
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        detail = f'Unable to find the {model.__name__} with {field} equal to {value}.'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data.update({
            "resource": model.__name__,
            "field": field,
            "value": value
        })
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="MODEL_FIELD_NOT_FOUND",
            error_type="ModelFieldNotFoundException",
            extras=extras_data,
            headers=headers
        )
        self.model = model
        self.field = field
        self.value = value


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


class ModelAlreadyExistsError(CoreException, Generic[ModelType]):
    """
    Ошибка, возникающая при попытке создать модель с существующим уникальным полем.
    """
    def __init__(
        self,
        model: type[ModelType],
        field: str,
        message: str,
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        detail = f'Model {model.__name__} with {field} already exists: {message}'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data.update({
            "resource": model.__name__,
            "field": field,
            "message": message
        })
        
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="MODEL_ALREADY_EXISTS",
            error_type="ModelAlreadyExistsError",
            extras=extras_data,
            headers=headers
        )
        self.model = model
        self.field = field
        self.message = message


class ValidationError(CoreException):
    """
    Ошибка валидации (для ручного вызова в бизнес-логике).
    """
    def __init__(
        self,
        field: str | list[str],
        message: str,
        error_code: str = "VALIDATION_ERROR",
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        detail = f'Validation error in {field}: {message}'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data.update({
            "field": field,
            "message": message
        })
        
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            error_type="ValidationError",
            extras=extras_data,
            headers=headers
        )
        self.field = field
        self.message = message


class SortingFieldNotFoundError(CoreException):
    """
    Ошибка, возникающая при невозможности найти поле для сортировки.
    """
    def __init__(
        self,
        field: str,
        headers: Dict[str, Any] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        detail = f'Failed to find a field to sort: {field}'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data["field"] = field
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="SORTING_FIELD_NOT_FOUND",
            error_type="SortingFieldNotFoundError",
            extras=extras_data,
            headers=headers
        )
        self.field = field


class FileNotFound(CoreException):
    """
    Исключение, если файл не найден.
    """
    def __init__(
        self,
        path: str,
        headers: Dict[str, str] | None = None,
        extras: Dict[str, Any] | None = None
    ) -> None:
        detail = f'File {path} not found.'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data["path"] = path
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="FILE_NOT_FOUND",
            error_type="FileNotFound",
            extras=extras_data,
            headers=headers
        )
        self.path = path


class ExternalServiceError(CoreException):
    """
    Базовый класс для ошибок межмикросервисного взаимодействия.
    """
    def __init__(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        detail: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        extras: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None
    ):
        extras_data = extras or {}
        extras_data.update({
            "service": service_name,
            "method": method,
            "endpoint": endpoint
        })
        
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code=error_code,
            error_type="ExternalServiceError",
            extras=extras_data,
            headers=headers
        )
        self.service_name = service_name
        self.method = method
        self.endpoint = endpoint


class ExternalServiceTimeoutError(ExternalServiceError):
    """
    Ошибка таймаута при взаимодействии с внешним сервисом.
    """
    def __init__(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        detail: str = "Service request timed out",
        extras: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None
    ):
        super().__init__(
            service_name=service_name,
            method=method,
            endpoint=endpoint,
            detail=detail,
            error_code="SERVICE_TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            extras=extras,
            headers=headers
        )


class ExternalServiceNotFoundError(ExternalServiceError):
    """
    Ошибка 404 при взаимодействии с внешним сервисом.
    """
    def __init__(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        detail: str = "Resource not found in external service",
        extras: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None
    ):
        super().__init__(
            service_name=service_name,
            method=method,
            endpoint=endpoint,
            detail=detail,
            error_code="EXTERNAL_RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            extras=extras,
            headers=headers
        )


class ExternalServiceUnauthorizedError(ExternalServiceError):
    """
    Ошибка 401 при взаимодействии с внешним сервисом.
    """
    def __init__(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        detail: str = "Unauthorized access to external service",
        extras: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None
    ):
        super().__init__(
            service_name=service_name,
            method=method,
            endpoint=endpoint,
            detail=detail,
            error_code="EXTERNAL_UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            extras=extras,
            headers=headers
        )


class ExternalServiceForbiddenError(ExternalServiceError):
    """
    Ошибка 403 при взаимодействии с внешним сервисом.
    """
    def __init__(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        detail: str = "Forbidden access to external service",
        extras: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None
    ):
        super().__init__(
            service_name=service_name,
            method=method,
            endpoint=endpoint,
            detail=detail,
            error_code="EXTERNAL_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            extras=extras,
            headers=headers
        )


class ExternalServiceConflictError(ExternalServiceError):
    """
    Ошибка 409 при взаимодействии с внешним сервисом.
    """
    def __init__(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        detail: str = "Conflict with external service resource",
        extras: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None
    ):
        super().__init__(
            service_name=service_name,
            method=method,
            endpoint=endpoint,
            detail=detail,
            error_code="EXTERNAL_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            extras=extras,
            headers=headers
        )