from fastapi import status 
import uuid
from typing import Optional
from shared.exceptions import CoreException

class CategoryLimitExceededError(CoreException):
    """
    Ошибка, возникающая при превышении лимита на количество категорий для персонажа.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        max_categories: Optional[int] = None,
        detail: str = None,
        error_code: str = "CATEGORY_LIMIT_EXCEEDED",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            if max_categories is not None:
                detail = f"Category limit exceeded. Maximum {max_categories} categories allowed per character."
            else:
                detail = "Category limit exceeded. Please delete some categories before creating a new one."
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        if max_categories is not None:
            extras["max_categories"] = max_categories
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="CategoryLimitExceededError",
            extras=extras,
            headers=headers
        )

class CategoryCharacterLimitExceededError(CoreException):
    """
    Ошибка, возникающая при превышении лимита на количество персонажей в категории.
    """
    def __init__(
        self,
        category_id: Optional[uuid.UUID] = None,
        max_characters: Optional[int] = None,
        detail: str = None,
        error_code: str = "CATEGORY_CHARACTER_LIMIT_EXCEEDED",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            if max_characters is not None:
                detail = f"Category character limit exceeded. Maximum {max_characters} characters allowed in this category."
            else:
                detail = "Category character limit exceeded. Please remove some characters from this category."
        
        if extras is None:
            extras = {}
        
        if category_id is not None:
            extras["category_id"] = str(category_id)
        if max_characters is not None:
            extras["max_characters"] = max_characters
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="CategoryCharacterLimitExceededError",
            extras=extras,
            headers=headers
        )  

class CannotAddSelfToCategoryError(CoreException):
    """
    Ошибка, возникающая при попытке добавить самого себя в категорию.
    """
    def __init__(
        self,
        character_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        detail: str = None,
        error_code: str = "CANNOT_ADD_SELF_TO_CATEGORY",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Cannot add self to category. A character cannot be added to their own category."
        
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        if category_id is not None:
            extras["category_id"] = str(category_id)
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="CannotAddSelfToCategoryError",
            extras=extras,
            headers=headers
        ) 