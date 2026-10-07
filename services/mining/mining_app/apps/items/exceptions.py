import uuid
from decimal import Decimal

from fastapi import status

from shared.exceptions import CoreException


class InsufficientCharacterLevelError(CoreException):
    """
    Ошибка, возникающая при недостаточном уровне персонажа для крафта предмета.
    """
    def __init__(
        self,
        detail: str = "Insufficient character level to craft this item",
        error_code: str = "INSUFFICIENT_CHARACTER_LEVEL",
        required_level: int | None = None,
        current_level: int | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_level is not None:
            extras["required_level"] = required_level
        if current_level is not None:
            extras["current_level"] = current_level
            
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
    Ошибка, возникающая при слишком высокой усталости персонажа для крафта.
    """
    def __init__(
        self,
        detail: str = "Character is too tired to craft this item",
        error_code: str = "INSUFFICIENT_CHARACTER_TIREDNESS",
        required_tiredness: float | None = None,
        current_tiredness: float | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_tiredness is not None:
            extras["required_tiredness"] = required_tiredness
        if current_tiredness is not None:
            extras["current_tiredness"] = current_tiredness
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientCharacterTirednessError",
            extras=extras,
            headers=headers
        )

class ItemAlreadyCreatingError(CoreException):
    """
    Ошибка, возникающая при попытке начать крафт предмета, когда персонаж уже создает другой предмет.
    """
    def __init__(
        self,
        character_id: uuid.UUID | None = None,
        character_name: str | None = None,
        current_action_id: uuid.UUID | None = None,
        detail: str = "Character is already creating an item",
        error_code: str = "ITEM_ALREADY_CREATING",
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
            error_type="ItemAlreadyCreatingError",
            extras=extras,
            headers=headers
        )


class InsufficientCharacterDucatsForCityTradeShopError(CoreException):
    """
    Ошибка, возникающая при недостаточном количестве дукатов для покупки магазина.
    """
    def __init__(
        self,
        detail: str = "Insufficient character ducats to buy city trade shop",
        error_code: str = "INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP",
        required_ducats: int | None = None,
        current_ducats: int | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_ducats is not None:
            extras["required_ducats"] = required_ducats
        if current_ducats is not None:
            extras["current_ducats"] = current_ducats
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientCharacterDucatsForCityTradeShopError",
            extras=extras,
            headers=headers
        )


class InsufficientResourcesForCraftingError(CoreException):
    """
    Ошибка, возникающая при недостаточном количестве ресурсов для крафта.
    """
    def __init__(
        self,
        detail: str = "Insufficient resources to craft this item",
        error_code: str = "INSUFFICIENT_RESOURCES_FOR_CRAFTING",
        missing_resources: dict | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if missing_resources is not None:
            extras["missing_resources"] = missing_resources
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientResourcesForCraftingError",
            extras=extras,
            headers=headers
        )


class CharacterNotInBuildingLocationError(CoreException):
    """
    Ошибка, возникающая когда персонаж не находится в локации здания для крафта.
    """
    def __init__(
        self,
        detail: str = "Character is not in the building location required for crafting",
        error_code: str = "CHARACTER_NOT_IN_BUILDING_LOCATION",
        required_location: str | None = None,
        current_location: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_location is not None:
            extras["required_location"] = required_location
        if current_location is not None:
            extras["current_location"] = current_location
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CharacterNotInBuildingLocationError",
            extras=extras,
            headers=headers
        )


class NotEnoughDucatsError(CoreException):
    """
    Ошибка, возникающая при недостаточном количестве дукатов.
    """
    def __init__(
        self,
        detail: str = "Not enough ducats",
        error_code: str = "NOT_ENOUGH_DUCATS",
        required_ducats: Decimal | None = None,
        current_ducats: Decimal | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_ducats is not None:
            extras["required_ducats"] = required_ducats
        if current_ducats is not None:
            extras["current_ducats"] = current_ducats
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="NotEnoughDucatsError",
            extras=extras,
            headers=headers
        )



class InsufficientCharacterLevelForCityTradeShopError(CoreException):
    """
    Ошибка, возникающая при недостаточном уровне персонажа для покупки магазина.
    """
    def __init__(
        self,
        detail: str = "Insufficient character level to buy city trade shop",
        error_code: str = "INSUFFICIENT_CHARACTER_LEVEL_FOR_CITY_TRADE_SHOP",
        required_level: int | None = None,
        current_level: int | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_level is not None:
            extras["required_level"] = required_level
        if current_level is not None:
            extras["current_level"] = current_level
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientCharacterLevelForCityTradeShopError",
            extras=extras,
            headers=headers
        )



class CharacterNotInItemLocationError(CoreException):
    """
    Ошибка, возникающая когда персонаж не находится в локации предмета.
    """
    def __init__(
        self,
        detail: str = "Character is not in the item location",
        error_code: str = "CHARACTER_NOT_IN_ITEM_LOCATION",
        required_location: str | None = None,
        current_location: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_location is not None:
            extras["required_location"] = required_location
        if current_location is not None:
            extras["current_location"] = current_location
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CharacterNotInItemLocationError",
            extras=extras,
            headers=headers
        )



class ShopCapacityExceededError(CoreException):
    """
    Ошибка, возникающая при превышении вместимости магазина.
    """
    def __init__(
        self,
        detail: str = "Shop capacity exceeded",
        error_code: str = "SHOP_CAPACITY_EXCEEDED",
        current_capacity: int | None = None,
        max_capacity: int | None = None,
        location_slug: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if current_capacity is not None:
            extras["current_capacity"] = current_capacity
        if max_capacity is not None:
            extras["max_capacity"] = max_capacity
        if location_slug is not None:
            extras["location_slug"] = location_slug
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="ShopCapacityExceededError",
            extras=extras,
            headers=headers
        )



class ItemNotForSaleError(CoreException):
    """
    Ошибка, возникающая когда предмет не выставлен на продажу.
    """
    def __init__(
        self,
        detail: str = "Item is not for sale",
        error_code: str = "ITEM_NOT_FOR_SALE",
        item_id: uuid.UUID | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if item_id is not None:
            extras["item_id"] = str(item_id)
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
            error_type="ItemNotForSaleError",
            extras=extras,
            headers=headers
        )


class InsufficientDucatsToBuyError(CoreException):
    """
    Ошибка, возникающая при недостаточном количестве дукатов для покупки.
    """
    def __init__(
        self,
        detail: str = "Insufficient ducats to buy item",
        error_code: str = "INSUFFICIENT_DUCATS_TO_BUY",
        required_ducats: Decimal | None = None,
        current_ducats: Decimal | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if required_ducats is not None:
            extras["required_ducats"] = required_ducats
        if current_ducats is not None:
            extras["current_ducats"] = current_ducats
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="InsufficientDucatsToBuyError",
            extras=extras,
            headers=headers
        )



class CityTradingShopLicenseExpiredError(CoreException):
    """
    Ошибка, возникающая когда лицензия магазина истекла.
    """
    def __init__(
        self,
        detail: str = "Истек срок лицензии",
        error_code: str = "CITY_TRADING_SHOP_LICENSE_EXPIRED",
        location_slug: str | None = None,
        end_license: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if location_slug is not None:
            extras["location_slug"] = location_slug
        if end_license is not None:
            extras["end_license"] = end_license
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CityTradingShopLicenseExpiredError",
            extras=extras,
            headers=headers
        )


class CityTradingShopNotFoundError(CoreException):
    """
    Ошибка, возникающая когда магазин не найден в локации.
    """
    def __init__(
        self,
        detail: str = "City trading shop not found in this location",
        error_code: str = "CITY_TRADING_SHOP_NOT_FOUND",
        location_slug: str | None = None,
        character_id: uuid.UUID | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if location_slug is not None:
            extras["location_slug"] = location_slug
        if character_id is not None:
            extras["character_id"] = str(character_id)
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
            error_type="CityTradingShopNotFoundError",
            extras=extras,
            headers=headers
        )



class RecipeNotFoundError(CoreException):
    """
    Ошибка, возникающая когда рецепт не найден у персонажа.
    """
    def __init__(
        self,
        detail: str = "Рецепт не найден",
        error_code: str = "RECIPE_NOT_FOUND",
        character_id: uuid.UUID | None = None,
        item_slug: str | None = None,
        quantity: int | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if character_id is not None:
            extras["character_id"] = str(character_id)
        if item_slug is not None:
            extras["item_slug"] = item_slug
        if quantity is not None:
            extras["quantity"] = quantity
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
            error_type="RecipeNotFoundError",
            extras=extras,
            headers=headers
        )

class NoCraftingLicenseError(CoreException):
    def __init__(
        self,
        location_slug: str,
        detail: str = "No active crafting license for this location",
        error_code: str = "NO_CRAFTING_LICENSE",
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        extras["location_slug"] = location_slug
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="NoCraftingLicenseError",
            extras=extras,
            headers=headers
        )

class ItemCraftAlreadyStartedError(CoreException):
    """
    Ошибка, возникающая при попытке начать новый крафт предмета,
    который уже находится в процессе создания (CharacterStartCreatingItem существует).
    """
    def __init__(
        self,
        detail: str = "Крафт этого товара уже начат — продолжите его во вкладке 'Изготовление'",
        error_code: str = "ITEM_CRAFT_ALREADY_STARTED",
        item_slug: str | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if item_slug is not None:
            extras["item_slug"] = item_slug
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="ItemCraftAlreadyStartedError",
            extras=extras,
            headers=headers
        )

class CharacterWeightExceededError(CoreException):
    """
    Ошибка, возникающая при превышении максимального веса персонажа.
    """
    def __init__(
        self,
        detail: str = "У вас нет места в рюкзаке",
        error_code: str = "CHARACTER_WEIGHT_EXCEEDED",
        current_weight: int | None = None,
        max_weight: int | None = None,
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        
        if current_weight is not None:
            extras["current_weight"] = current_weight
        if max_weight is not None:
            extras["max_weight"] = max_weight
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            error_type="CharacterWeightExceededError",
            extras=extras,
            headers=headers
        )

class SalePriceTooLowError(CoreException):
    """
    Ошибка: цена продажи ниже половины базовой стоимости предмета.
    """
    def __init__(
        self,
        min_price: Decimal,
        error_code: str = "SALE_PRICE_TOO_LOW",
        extras: dict | None = None,
        headers: dict | None = None
    ) -> None:
        if extras is None:
            extras = {}
        extras["min_price"] = min_price

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя продать предмет ниже половины его базовой стоимости (мин. {min_price:.2f} дт.)",
            error_code=error_code,
            error_type="SalePriceTooLowError",
            extras=extras,
            headers=headers
        )