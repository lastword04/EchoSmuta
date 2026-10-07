# ============================================================
# Универсальная проверка требований предмета к персонажу
# (уровень, раса, характеристики)
# ============================================================
from ...core.utils.exceptions import ValidationError

RACE_LABELS = {
    'orc': 'Орк',
    'elf': 'Эльф',
    'human': 'Человек',
}

STAT_REQUIREMENTS = [
    # (ключ в parameters предмета, поле ИТОГОВОГО стата, форма Р.п.)
    ('required_strength', 'eff_power', 'Силы'),
    ('required_agility', 'eff_agility', 'Ловкости'),
    ('required_luck', 'eff_lucky', 'Удачи'),
]


def check_item_requirements(item, character) -> None:
    """
    Проверяет все требования предмета к персонажу.
    Бросает ValidationError при несоответствии.
    """
    # Уровень
    min_level = getattr(item, 'minimal_level', None) or 0
    if min_level and (character.level or 0) < min_level:
        raise ValidationError(
            field="level",
            message=f"Требуется {min_level}-й уровень"
        )

    # ─── Раса (нормализация: enum Race.ELF / 'ELF' / 'elf' → 'elf') ───
    def _norm_race(v):
        if v is None:
            return None
        if hasattr(v, 'value'):      # Python enum → берём value ('ELF')
            v = v.value
        return str(v).lower()

    item_race = _norm_race(getattr(item, 'race', None))
    char_race = _norm_race(getattr(character, 'race', None))
    if item_race and char_race and char_race != item_race:
        raise ValidationError(
            field="race",
            message=f"Этот эликсир доступен только расе {RACE_LABELS.get(item_race, item_race)}"
        )

    # Характеристики
    params = getattr(item, 'parameters', None) or {}
    for req_key, char_field, label in STAT_REQUIREMENTS:
        required = params.get(req_key) or 0
        if required:
            actual = getattr(character, char_field, 0) or 0
            if actual < required:
                raise ValidationError(
                    field=req_key,
                    message=f"Требуется {required} {label}"
                )