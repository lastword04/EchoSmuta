"""
Модуль для классификации и маппинга бонусов экипировки.

Определяет какие ключи из каталога предметов относятся к каким категориям бонусов:
- Flat статы (strength, agility, luck, health, mana) - влияют на effective_*
- Percent статы (*_percent) - сохраняются, не влияют на effective_*
- Боевые параметры (defense, damage, dodge, crit, reductions) - сохраняются для боя
- Магические параметры (magic_order_*) - сохраняются для магии
- Ограничения (required_*) - НЕ являются бонусами, только требования
"""

from enum import Enum
from typing import Any


class BonusCategory(str, Enum):
    """Категории бонусов экипировки"""
    FLAT_STAT = "flat_stat"  # Плоские статы: влияют на effective_*
    PERCENT_STAT = "percent_stat"  # Процентные статы: для отображения
    COMBAT = "combat"  # Боевые параметры: defense, damage, dodge, crit, reductions
    MAGIC = "magic"  # Магические параметры: magic_order_*
    REQUIREMENT = "requirement"  # Требования для экипировки: НЕ бонусы
    OTHER = "other"  # Прочие технические параметры


# Плоские статы из ability_parameters - влияют на effective_*
FLAT_STATS = {
    "strength",      # Сила
    "agility",       # Ловкость
    "luck",          # Удача
    "health",        # Здоровье (влияет на max_health)
    "mana",          # Мана (влияет на max_mana)
}

# Процентные статы из ability_parameters - НЕ влияют на effective_*, только отображаются
PERCENT_STATS = {
    "strength_percent",
    "agility_percent",
    "luck_percent",
    "health_percent",
    "mana_percent",
}

# Боевые параметры из parameters - сохраняются для использования в бою
COMBAT_PARAMS = {
    "defense",           # Защита
    "damage_min",        # Минимальный урон
    "damage_max",        # Максимальный урон
    "dodge_self",        # Уворот (свой)
    "crit_self",         # Крит (свой)
    "dodge_reduction",   # Снижение уворота противника
    "crit_reduction",    # Снижение крита противника
}

# Магические параметры из ability_parameters - для магических способностей
MAGIC_PARAMS = {
    "magic_order_1_self",
    "magic_order_2_self",
    "magic_order_3_self",
}

# Требования для экипировки из parameters - НЕ являются бонусами
REQUIREMENTS = {
    "required_strength",
    "required_agility",
    "required_luck",
}

# Технические параметры из parameters - НЕ являются бонусами
TECHNICAL_PARAMS = {
    "max_wear",
    "affinity",  # Для плащей
}


def categorize_bonus_key(key: str) -> BonusCategory:
    """
    Определяет категорию ключа бонуса.
    
    Args:
        key: Ключ параметра из ability_parameters или parameters
        
    Returns:
        Категория бонуса
        
    Examples:
        >>> categorize_bonus_key("strength")
        BonusCategory.FLAT_STAT
        >>> categorize_bonus_key("strength_percent")
        BonusCategory.PERCENT_STAT
        >>> categorize_bonus_key("defense")
        BonusCategory.COMBAT
        >>> categorize_bonus_key("required_strength")
        BonusCategory.REQUIREMENT
    """
    if key in FLAT_STATS:
        return BonusCategory.FLAT_STAT
    elif key in PERCENT_STATS:
        return BonusCategory.PERCENT_STAT
    elif key in COMBAT_PARAMS:
        return BonusCategory.COMBAT
    elif key in MAGIC_PARAMS:
        return BonusCategory.MAGIC
    elif key in REQUIREMENTS:
        return BonusCategory.REQUIREMENT
    elif key in TECHNICAL_PARAMS:
        return BonusCategory.OTHER
    else:
        return BonusCategory.OTHER


def is_bonus_key(key: str) -> bool:
    """
    Проверяет, является ли ключ бонусом (а не требованием или техническим параметром).
    
    Args:
        key: Ключ параметра
        
    Returns:
        True если это бонус, False если требование или технический параметр
    """
    category = categorize_bonus_key(key)
    return category not in (BonusCategory.REQUIREMENT, BonusCategory.OTHER)


def should_affect_effective_stats(key: str) -> bool:
    """
    Проверяет, должен ли бонус влиять на effective_* статы в Characters.
    
    Args:
        key: Ключ параметра
        
    Returns:
        True если бонус влияет на effective_strength/agility/luck/max_health/max_mana
    """
    return categorize_bonus_key(key) == BonusCategory.FLAT_STAT


# Маппинг ключей из каталога в формат с суффиксом _bonus для Characters/Frontend
CATALOG_KEY_TO_BONUS_KEY = {
    # Flat статы из ability_parameters -> *_bonus
    "strength": "strength_bonus",
    "agility": "agility_bonus",
    "luck": "luck_bonus",
    "health": "max_health_bonus",      # health влияет на max_health
    "mana": "max_mana_bonus",          # mana влияет на max_mana
    # tiredness не используется в каталоге, но если появится:
    "tiredness": "max_tiredness_bonus",
    
    # Percent статы остаются как есть (без маппинга)
    # "strength_percent": "strength_percent",
    # "agility_percent": "agility_percent",
    # и т.д.
    
    # Боевые параметры из parameters остаются как есть
    # "defense": "defense",
    # "damage_min": "damage_min",
    # и т.д.
    
    # Магические параметры остаются как есть
    # "magic_order_1_self": "magic_order_1_self",
    # и т.д.
}


def normalize_bonus_key(key: str) -> str:
    """
    Преобразует ключ из каталога в унифицированный ключ для equipment_bonuses.
    
    Применяет маппинг для flat статов (strength -> strength_bonus),
    остальные ключи остаются без изменений.
    
    Args:
        key: Ключ из каталога
        
    Returns:
        Нормализованный ключ для equipment_bonuses
        
    Examples:
        >>> normalize_bonus_key("strength")
        "strength_bonus"
        >>> normalize_bonus_key("health")
        "max_health_bonus"
        >>> normalize_bonus_key("defense")
        "defense"
        >>> normalize_bonus_key("strength_percent")
        "strength_percent"
    """
    return CATALOG_KEY_TO_BONUS_KEY.get(key, key)


def extract_bonuses_from_item(item_parameters: dict | None, item_ability_parameters: dict | None) -> dict[str, Any]:
    """
    Извлекает все бонусы из parameters и ability_parameters предмета.
    
    Применяет нормализацию ключей: strength -> strength_bonus, health -> max_health_bonus и т.д.
    
    Args:
        item_parameters: Словарь parameters из каталога (боевые + требования + технические)
        item_ability_parameters: Словарь ability_parameters из каталога (статы + проценты + магия)
        
    Returns:
        Словарь бонусов с нормализованными ключами {ключ: значение}
        
    Examples:
        >>> extract_bonuses_from_item(
        ...     {"defense": 10, "required_strength": 20, "max_wear": 50},
        ...     {"strength": 5, "health": 100}
        ... )
        {"defense": 10, "strength_bonus": 5, "max_health_bonus": 100}
    """
    bonuses = {}
    
    # Извлекаем из parameters (боевые параметры)
    if item_parameters:
        for key, value in item_parameters.items():
            if is_bonus_key(key) and isinstance(value, (int, float)):
                normalized_key = normalize_bonus_key(key)
                bonuses[normalized_key] = value
    
    # Извлекаем из ability_parameters (статы, проценты, магия)
    if item_ability_parameters:
        for key, value in item_ability_parameters.items():
            if is_bonus_key(key) and isinstance(value, (int, float)):
                normalized_key = normalize_bonus_key(key)
                bonuses[normalized_key] = value
    
    return bonuses
