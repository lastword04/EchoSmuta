from ...models import (
    StatModifier,
    MOD_FLAT,
    MOD_PERCENT,
    MOD_MULTIPLIER,
    CONTEXT_ALWAYS,
)


# Где на персонаже лежат базовые значения каждой статы.
# "strength" у нас исторически называется power в модели персонажа.
BASE_STAT_FIELDS = {
    "strength": "power",
    "agility": "agility",
    "lucky": "lucky",
    "max_health": "max_health",
    "max_mana": "max_mana",
    "max_tiredness": "max_tiredness",
}

# Ключи результата — то, к чему привык фронт
OUTPUT_KEYS = {
    "strength": "effective_power",
    "agility": "effective_agility",
    "lucky": "effective_lucky",
    "max_health": "effective_max_health",
    "max_mana": "effective_max_mana",
    "max_tiredness": "effective_max_tiredness",
}

# Эти статы фронт привык видеть целыми
INT_STATS = {"strength", "agility", "lucky"}


class StatsAggregator:
    """
    Применяет модификаторы к базовым статам.

    Формула для каждой статы:
        (база + сумма flat + база * сумма percent / 100) * произведение multiplier

    Проценты считаются от БАЗЫ (не от накопленного), проценты между собой
    складываются, множители между собой перемножаются. Порядок применения
    внутри типа не важен — результат предсказуем и не зависит от того,
    что игрок выпил раньше.
    """

    @staticmethod
    def calculate_effective_stats(
        character,
        modifiers: list[StatModifier],
        context: str = "map_only",
    ) -> dict:
        # Личные модификаторы + модификаторы запрошенного контекста
        active = [
            m for m in modifiers
            if m.context == CONTEXT_ALWAYS or m.context == context
        ]

        result = {}
        for stat, field in BASE_STAT_FIELDS.items():
            base = float(getattr(character, field))

            sum_flat = 0.0
            sum_percent = 0.0
            product_mult = 1.0

            for m in active:
                if m.stat != stat:
                    continue
                if m.modifier_type == MOD_FLAT:
                    sum_flat += m.value
                elif m.modifier_type == MOD_PERCENT:
                    sum_percent += m.value
                elif m.modifier_type == MOD_MULTIPLIER:
                    product_mult *= m.value

            value = (base + sum_flat + base * sum_percent / 100) * product_mult

            if stat in INT_STATS:
                result[OUTPUT_KEYS[stat]] = int(round(value))
            else:
                result[OUTPUT_KEYS[stat]] = round(value, 2)

        return result