from ...models import StatModifier, MOD_FLAT, CONTEXT_ALWAYS


# Какие ключи из equipment_bonuses на какие статы влияют.
# Сейчас все бонусы экипировки — flat. Появятся процентные — добавим сюда.
EQUIPMENT_KEY_TO_STAT = {
    "strength_bonus": "strength",
    "agility_bonus": "agility",
    "luck_bonus": "lucky",
    "max_health_bonus": "max_health",
    "max_mana_bonus": "max_mana",
    "max_tiredness_bonus": "max_tiredness",
}


class EquipmentCollector:
    """Собирает модификаторы из экипировки персонажа."""

    async def get_modifiers(self, character) -> list[StatModifier]:
        """
        Принимает объект персонажа (уже загруженный из БД).
        В базу не ходит: бонусы экипировки лежат прямо на персонаже.
        """
        bonuses = character.equipment_bonuses or {}
        modifiers = []

        for key, stat in EQUIPMENT_KEY_TO_STAT.items():
            value = bonuses.get(key, 0)
            if not value:
                continue
            modifiers.append(
                StatModifier(
                    source_type="equipment",
                    source_id="equipment",  # у экипировки бонусы идут целиком, без единого ID
                    stat=stat,
                    value=value,
                    modifier_type=MOD_FLAT,
                    context=CONTEXT_ALWAYS,
                )
            )

        return modifiers