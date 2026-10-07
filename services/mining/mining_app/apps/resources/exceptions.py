import uuid

from fastapi import status

from shared.exceptions import CoreException


class ResourceAlreadyMiningError(CoreException):
    """
    Ошибка, возникающая при попытке начать добычу ресурса, когда персонаж уже добывает другой ресурс.
    """
    def __init__(
        self,
        character_id: uuid.UUID | None = None,
        character_name: str | None = None,
        current_action_id: uuid.UUID | None = None,
        detail: str = "Character is already mining a resource",
        error_code: str = "RESOURCE_ALREADY_MINING",
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        if character_name is not None:
            extras["character_name"] = character_name
        if current_action_id is not None:
            extras["current_action_id"] = str(current_action_id)
            
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
            error_type="ResourceAlreadyMiningError",
            extras=extras,
            headers=headers
        )


class InsufficientCharacterLevelError(CoreException):
    """
    Ошибка, возникающая при недостаточном уровне персонажа для добычи ресурса.
    """
    def __init__(
        self,
        detail: str = "Insufficient character level to mine this resource",
        error_code: str = "INSUFFICIENT_CHARACTER_LEVEL",
        required_level: int | None = None,
        current_level: int | None = None,
        resource_name: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_level is not None:
            extras["required_level"] = required_level
        if current_level is not None:
            extras["current_level"] = current_level
        if resource_name is not None:
            extras["resource_name"] = resource_name
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientCharacterLevelError",
            extras=extras,
            headers=headers
        )


class InsufficientCharacterTirednessError(CoreException):
    """
    Ошибка, возникающая при недостаточном количестве усталости для добычи ресурса.
    """
    def __init__(
        self,
        detail: str = "Insufficient character tiredness to perform mining",
        error_code: str = "INSUFFICIENT_CHARACTER_TIREDNESS",
        required_tiredness: float | None = None,
        current_tiredness: float | None = None,
        resource_name: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_tiredness is not None:
            extras["required_tiredness"] = required_tiredness
        if current_tiredness is not None:
            extras["current_tiredness"] = current_tiredness
        if resource_name is not None:
            extras["resource_name"] = resource_name
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientCharacterTirednessError",
            extras=extras,
            headers=headers
        )