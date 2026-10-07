import uuid
from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status

from ..db import Base

ModelType = TypeVar('ModelType', bound=Base)


class CoreException(HTTPException):
    """
    Базовый класс для всех исключений приложения.
    """
    def __init__(self, status_code: int, detail: str, headers: dict[str, Any] | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

    def to_dict(self) -> dict:
        return {"detail": self.detail}


class ModelNotFoundException(CoreException, Generic[ModelType]):
    """
    Исключение не найденной модели.
    """
    def __init__(
        self,
        model: type[ModelType],
        model_id: uuid.UUID | None = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        detail = (
            f'Unable to find the {model.__name__} with id {model_id}.'
            if model_id is not None
            else f'{model.__name__} id not found.'
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)


class ModelFieldNotFoundException(CoreException, Generic[ModelType]):
    """
    Исключение, возникающее при отсутствии модели с указанным значением поля.
    """
    def __init__(
        self,
        model: type[ModelType],
        field: str,
        value: Any,
        headers: dict[str, Any] | None = None,
    ) -> None:
        detail = f'Unable to find the {model.__name__} with {field} equal to {value}.'
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)


class PermissionDeniedError(CoreException):
    """
    Ошибка, возникающая при недостатке прав для выполнения действия.
    """
    def __init__(
        self,
        detail: str = 'Insufficient rights to perform the action',
        headers: dict[str, Any] | None = None
    ) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)


class ModelAlreadyExistsError(CoreException):
    """
    Ошибка, возникающая при попытке создать модель с существующим уникальным полем.
    """
    def __init__(self,
                 model: type[ModelType],
                 field: str, 
                 message: str, 
                 headers: dict[str, Any] | None = None) -> None:
        detail = f'Model {model.__name__} with {field} already exists: {message}'
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, headers=headers)
        self.field = field


class ValidationError(CoreException):
    """
    Ошибка валидации.
    """
    def __init__(self, field: str | list[str], message: str, headers: dict[str, Any] | None = None) -> None:
        detail = f'Validation error in {field}: {message}'
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail, headers=headers)
        self.field = field


class SortingFieldNotFoundError(CoreException):
    """
    Ошибка, возникающая при невозможности найти поле для сортировки.
    """
    def __init__(self, 
                 field: str, 
                 headers: dict[str, Any] | None = None) -> None:
        detail = f'Failed to find a field to sort: {field}'
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)
        self.field = field


class FileNotFound(CoreException):
    """
    Исключение, если файл не найден.
    """
    def __init__(self, path: str, headers: dict[str, str] | None = None) -> None:
        detail = f'File {path} not found.'
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)
        self.path = path
