from fastapi import status
from typing import Any
from shared.exceptions import CoreException
from .enums import MenuItem


class DuplicateMenuItemsError(CoreException):
    """
    Исключение, возникающее при попытке установить одинаковые элементы меню.
    """
    def __init__(
        self,
        first_item: MenuItem,
        second_item: MenuItem,
        headers: dict[str, Any] | None = None,
        extras: dict[str, Any] | None = None
    ) -> None:
        detail = f'First item: {first_item.value} and second item: {second_item.value} must be different.'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data.update({
            "first_item": first_item.name if hasattr(first_item, 'name') else str(first_item),
            "second_item": second_item.name if hasattr(second_item, 'name') else str(second_item),
            "first_item_value": first_item.value if hasattr(first_item, 'value') else str(first_item),
            "second_item_value": second_item.value if hasattr(second_item, 'value') else str(second_item)
        })
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="DUPLICATE_MENU_ITEMS",
            error_type="DuplicateMenuItemsError",
            extras=extras_data,
            headers=headers
        )
        self.first_item = first_item
        self.second_item = second_item