from dataclasses import dataclass
from decimal import Decimal

from shared.enums import Race

from ...enums import ItemType


@dataclass(frozen=True)
class ProductionItem:
    name: str
    slug: str
    item_type: ItemType
    location_slug: str
    price: Decimal
    weight: int
    max_wear: int
    craft_stages: int | None
    craft_experience: int | None
    minimal_level: int
    parameters: dict
    ability_parameters: dict | None = None
    race: Race | None = None
    components: tuple[tuple[str, int], ...] = ()


def requirements(level: int, strength: int = 0, agility: int = 0, luck: int = 0, **parameters: object) -> dict:
    result = {
        "required_strength": strength,
        "required_agility": agility,
        "required_luck": luck,
        "max_wear": parameters.pop("max_wear"),
    }
    result.update(parameters)
    return result


# =============================================================================
# КУЗНИЦА (1.13.forge)
# =============================================================================

# --- ЩИТЫ (SHIELD) ---

FORGE_SHIELDS = (
    # Уровень 1
    ProductionItem("Деревянный Щит", "i.shield.13.1.wooden-shield", ItemType.SHIELD, "1.13.forge", 12, 20, 20, None, None, 1, requirements(1, defense=4, max_wear=20)),

    # Уровень 2
    ProductionItem("Щит Лесника", "i.shield.13.2.forest-shield", ItemType.SHIELD, "1.13.forge", 30, 20, 30, None, None, 2, requirements(2, defense=6, max_wear=30)),

    # Уровень 3
    ProductionItem("Щит Блеска", "i.shield.13.3.shine-shield", ItemType.SHIELD, "1.13.forge", 125, 50, 40, None, None, 3, requirements(3, 14, defense=8, dodge_reduction=-0.10, crit_reduction=-0.05, max_wear=40)),
    ProductionItem("Щит Отпора", "i.shield.13.3.rebuke-shield", ItemType.SHIELD, "1.13.forge", 125, 50, 40, None, None, 3, requirements(3, luck=14, defense=8, dodge_reduction=-0.15, max_wear=40)),
    ProductionItem("Щит Привязанности", "i.shield.13.3.attachment-shield", ItemType.SHIELD, "1.13.forge", 125, 50, 40, None, None, 3, requirements(3, agility=14, defense=8, crit_reduction=-0.15, max_wear=40)),

    # Уровень 5
    ProductionItem("Щит Гордости Эльфа", "i.shield.13.5.elf-pride-shield", ItemType.SHIELD, "1.13.forge", 180, 80, 50, 6, 1, 5, requirements(5, agility=18, defense=13, dodge_reduction=-0.10, crit_reduction=-0.30, max_wear=50), {"health": 10, "strength": 2}, components=(("iron", 105), ("zinc", 40))),
    ProductionItem("Щит Контраста", "i.shield.13.5.contrast-shield", ItemType.SHIELD, "1.13.forge", 180, 80, 50, 6, 1, 5, requirements(5, luck=18, defense=13, dodge_reduction=-0.30, crit_reduction=-0.10, max_wear=50), {"health": 10, "strength": 2}, components=(("iron", 90), ("mica", 45))),
    ProductionItem("Щит ТриДесятков", "i.shield.13.5.three-dozens-shield", ItemType.SHIELD, "1.13.forge", 180, 80, 50, 6, 1, 5, requirements(5, 18, defense=13, dodge_reduction=-0.20, crit_reduction=-0.20, max_wear=50), {"health": 10, "agility": 1, "luck": 1}, components=(("iron", 110), ("tin", 15))),

    # Уровень 7
    ProductionItem("Щит Великана", "i.shield.13.7.giant-shield", ItemType.SHIELD, "1.13.forge", 330, 120, 60, 8, 2, 7, requirements(7, 42, 25, 25, defense=18, dodge_reduction=-0.10, crit_reduction=-0.10, max_wear=60), {"health": 200, "strength": 4}, components=(("iron", 230), ("copper", 100))),
    ProductionItem("Щит Великой Защиты", "i.shield.13.7.great-defense-shield", ItemType.SHIELD, "1.13.forge", 300, 100, 55, 8, 2, 7, requirements(7, 32, 27, 27, defense=18, dodge_reduction=-0.40, crit_reduction=-0.40, max_wear=55), {"strength": 2, "agility": 2, "luck": 2}, components=(("iron", 230), ("sulfur", 90))),
    ProductionItem("Щит Несокрушимости", "i.shield.13.7.indestructibility-shield", ItemType.SHIELD, "1.13.forge", 300, 120, 60, 8, 2, 7, requirements(7, 27, 25, 40, defense=22, dodge_reduction=-0.10, crit_reduction=-0.50, max_wear=60), {"health": 20, "agility": 1, "luck": 2}, components=(("iron", 200), ("zinc", 60))),
    ProductionItem("Щит Ответной Атаки", "i.shield.13.7.retaliation-shield", ItemType.SHIELD, "1.13.forge", 300, 100, 60, 8, 2, 7, requirements(7, 30, 30, 30, defense=20, dodge_reduction=-0.15, crit_reduction=-0.15, max_wear=60), {"health": 75, "strength": 3, "agility": 1, "luck": 1}, components=(("iron", 230), ("silicon", 90))),
    ProductionItem("Щит Примирения", "i.shield.13.7.reconciliation-shield", ItemType.SHIELD, "1.13.forge", 340, 140, 65, 8, 2, 7, requirements(7, 37, 26, 26, defense=22, dodge_reduction=-0.20, crit_reduction=-0.20, max_wear=65), {"health": 25, "agility": 3, "luck": 3}, components=(("iron", 250), ("tin", 20), ("skin-gro", 10))),
    ProductionItem("Щит Стойкости", "i.shield.13.7.fortitude-shield", ItemType.SHIELD, "1.13.forge", 300, 120, 60, 8, 2, 7, requirements(7, 27, 40, 25, defense=22, dodge_reduction=-0.50, crit_reduction=-0.10, max_wear=60), {"health": 20, "agility": 2, "luck": 1}, components=(("iron", 215), ("mica", 60))),
    ProductionItem("Щит Опровержения", "i.shield.13.7.refutation-shield", ItemType.SHIELD, "1.13.forge", 350, 140, 65, 8, 2, 7, requirements(7, 30, 24, 38, defense=22, dodge_reduction=-0.40, max_wear=65), {"strength": 3, "agility": 3}, components=(("iron", 240), ("mica", 60), ("skin-shishiga", 10))),
    ProductionItem("Щит Воспрепятствия", "i.shield.13.7.obstruction-shield", ItemType.SHIELD, "1.13.forge", 350, 140, 65, 8, 2, 7, requirements(7, 30, 38, 24, defense=22, crit_reduction=-0.40, max_wear=65), {"strength": 3, "luck": 3}, components=(("iron", 245), ("zinc", 55), ("skin-skorpion", 10))),

    # Уровень 9
    ProductionItem("Щит Снисхождения", "i.shield.13.9.condescension-shield", ItemType.SHIELD, "1.13.forge", 620, 140, 65, 10, 3, 9, requirements(9, 42, 25, 35, defense=28, dodge_reduction=-0.50, crit_reduction=-0.50, max_wear=65), {"strength": 4, "luck": 2}, components=(("iron", 360), ("copper", 120), ("skin-lord-zverozhab", 15))),
    ProductionItem("Щит Опыта", "i.shield.13.9.experience-shield", ItemType.SHIELD, "1.13.forge", 650, 160, 70, 10, 3, 9, requirements(9, 30, 30, 45, defense=32, dodge_reduction=-0.50, max_wear=70), {"health": 100, "strength": 6}, components=(("iron", 355), ("zinc", 120), ("skin-zlatoglav", 25))),
    ProductionItem("Щит Рассудительности", "i.shield.13.9.judiciousness-shield", ItemType.SHIELD, "1.13.forge", 650, 160, 70, 10, 3, 9, requirements(9, 32, 42, 30, defense=32, crit_reduction=-0.50, max_wear=70), {"health": 60, "strength": 2, "agility": 2, "luck": 2}, components=(("iron", 350), ("mica", 125), ("skin-kluvozyb", 25))),
    ProductionItem("Щит Покорности", "i.shield.13.9.submission-shield", ItemType.SHIELD, "1.13.forge", 600, 150, 70, 10, 3, 9, requirements(9, 48, 30, 30, defense=30, dodge_reduction=-0.40, crit_reduction=-0.60, max_wear=70), {"health": 100, "strength": 3}, components=(("iron", 360), ("tin", 40), ("skin-zverozhab", 25))),

    # Уровень 11
    ProductionItem("Щит Вековых Лесов", "i.shield.13.11.ancient-forest-shield", ItemType.SHIELD, "1.13.forge", 1100, 180, 80, 12, 4, 11, requirements(11, 45, 52, 37, defense=37, crit_reduction=-0.65, max_wear=80), {"health": 70, "strength": 2, "agility": 4, "luck": 2}, components=(("iron", 520), ("mica", 170), ("skin-morena", 25))),
    ProductionItem("Щит Теней", "i.shield.13.11.shadow-shield", ItemType.SHIELD, "1.13.forge", 950, 175, 80, 12, 4, 11, requirements(11, 80, 35, 35, defense=32, dodge_reduction=-0.30, crit_reduction=-0.30, max_wear=80), {"health": 200, "strength": 6}, components=(("iron", 470), ("zinc", 135), ("skin-big-gro", 25))),
    ProductionItem("Щит Вечного Сумрака", "i.shield.13.11.eternal-twilight-shield", ItemType.SHIELD, "1.13.forge", 1100, 180, 80, 12, 4, 11, requirements(11, 45, 37, 52, defense=37, dodge_reduction=-0.65, max_wear=80), {"health": 70, "strength": 2, "agility": 2, "luck": 4}, components=(("iron", 495), ("zinc", 140), ("skin-red-skorpion", 25), ("skin-lord-zverozhab", 10))),
    ProductionItem("Щит Отца Гор", "i.shield.13.11.father-of-mountains-shield", ItemType.SHIELD, "1.13.forge", 1100, 175, 75, 12, 4, 11, requirements(11, 55, 40, 40, defense=33, dodge_reduction=-0.65, crit_reduction=-0.65, max_wear=75), {"strength": 4, "agility": 2, "luck": 2}, components=(("iron", 540), ("tin", 65), ("skin-zlatogriz", 25))),
    ProductionItem("Щит Первобытной Ярости", "i.shield.13.11.primordial-fury-shield", ItemType.SHIELD, "1.13.forge", 1050, 180, 80, 12, 4, 11, requirements(11, 60, 37, 37, defense=35, dodge_reduction=-0.35, crit_reduction=-0.35, max_wear=80), {"health": 90, "strength": 4, "agility": 2, "luck": 2}, components=(("iron", 500), ("mica", 165), ("skin-kluvoklik", 25))),
)

# --- ОРУЖИЕ (WEAPON) ---

def _weapons() -> tuple[ProductionItem, ...]:
    rows = (
        # Уровень 1
        ("Охотничий Нож", "i.weapon.13.1.hunting-knife", 15, 20, 20, None, None, 1, 0, 0, 0, 4, 6, 0, 0, None, ()),
        ("Генеральский Кинжал", "i.weapon.13.1.general-dagger", 17, 20, 20, None, None, 1, 0, 0, 0, 4, 5, .05, .05, None, ()),

        # Уровень 2
        ("Тяжелый Узорный Меч", "i.weapon.13.2.heavy-patterned-sword", 50, 40, 30, None, None, 2, 8, 0, 0, 7, 9, .10, 0, {"strength_percent": .05}, ()),
        ("Меч Указания", "i.weapon.13.2.instruction-sword", 50, 40, 30, None, None, 2, 0, 0, 8, 7, 9, .10, .05, None, ()),
        ("Легкий Эльфийский Меч", "i.weapon.13.2.light-elven-sword", 50, 40, 30, None, None, 2, 0, 11, 0, 7, 9, .15, 0, None, ()),

        # Уровень 4
        ("Меч Постоянства", "i.weapon.13.4.constancy-sword", 170, 70, 45, 5, 1, 4, 15, 0, 0, 15, 17, .15, 0, {"strength": 2, "strength_percent": .10, "agility": 1}, (("iron", 110), ("sulfur", 25), ("copper", 30))),
        ("Меч Уверенности", "i.weapon.13.4.confidence-sword", 170, 70, 45, 5, 1, 4, 0, 20, 0, 15, 17, .15, 0, {"strength": 1, "strength_percent": .10, "agility": 2}, (("iron", 115), ("sulfur", 30), ("copper", 25))),
        ("Меч Удара", "i.weapon.13.4.strike-sword", 170, 70, 45, 5, 1, 4, 0, 0, 15, 15, 17, .15, .10, {"strength": 1, "agility": 1, "luck": 1}, (("iron", 100), ("sulfur", 30), ("copper", 30))),

        # Уровень 6
        ("Меч Ветра", "i.weapon.13.6.wind-sword", 220, 85, 60, 7, 2, 6, 0, 25, 0, 22, 26, .25, 0, {"strength": 1, "strength_percent": .05, "agility": 3, "luck": 1}, (("iron", 125), ("copper", 35), ("silicon", 30), ("beech", 30))),
        ("Меч Доблести", "i.weapon.13.6.valor-sword", 220, 85, 60, 7, 2, 6, 22, 0, 0, 20, 24, .20, 0, {"strength": 2, "strength_percent": .15, "agility": 2, "luck": 1}, (("iron", 140), ("copper", 30), ("silicon", 30), ("beech", 30))),
        ("Меч Лезвие Смерти", "i.weapon.13.6.death-blade-sword", 220, 85, 60, 7, 2, 6, 0, 0, 22, 21, 25, .15, .20, {"strength": 1, "agility": 2, "luck": 2}, (("iron", 125), ("copper", 40), ("silicon", 30), ("beech", 20))),

        # Уровень 8
        ("Меч Исключения", "i.weapon.13.8.exclusion-sword", 420, 100, 70, 9, 3, 8, 35, 40, 0, 28, 33, .30, .15, {"strength": 2, "agility": 3, "luck": 2}, (("iron", 200), ("copper", 50), ("zinc", 30), ("spruce", 20))),
        ("Меч Отца Гор", "i.weapon.13.8.father-of-mountains-sword", 450, 100, 70, 9, 3, 8, 35, 45, 0, 29, 35, .40, 0, {"strength": 3, "strength_percent": .05, "agility": 3}, (("iron", 200), ("copper", 45), ("zinc", 25), ("mahogany", 15))),

        # Уровень 10
        ("Меч Вечного Сна", "i.weapon.13.10.eternal-sleep-sword", 720, 120, 70, 11, 5, 10, 45, 45, 45, 33, 38, .45, .25, {"strength": 3, "agility": 3, "luck": 3}, (("iron", 250), ("copper", 65), ("tin", 55), ("beech", 50))),
        ("Меч Пробуждения", "i.weapon.13.10.awakening-sword", 750, 120, 70, 11, 5, 10, 45, 60, 0, 35, 41, .50, 0, {"strength": 6, "strength_percent": .20, "agility": 2, "luck": 1}, (("iron", 320), ("copper", 70), ("tin", 50), ("oak", 35))),
        ("Меч Острота Мысли", "i.weapon.13.10.sharpness-of-mind-sword", 770, 120, 70, 11, 5, 10, 45, 67, 0, 35, 40, .60, 0, {"strength": 4, "strength_percent": .05, "agility": 6}, (("iron", 305), ("copper", 65), ("tin", 55), ("birch", 35))),

        # Уровень 12
        ("Меч Сумеречного Аббата", "i.weapon.13.12.twilight-abbot-sword", 1170, 135, 80, 13, 7, 12, 55, 70, 0, 43, 49, .55, .20, {"strength": 9, "strength_percent": .15, "agility": 2, "luck": 3}, (("iron", 475), ("copper", 100), ("silicon", 70), ("tin", 60), ("birch", 80))),
        ("Меч Шепот Смерти", "i.weapon.13.12.death-whisper-sword", 1200, 135, 80, 13, 7, 12, 55, 80, 0, 44, 48, .65, 0, {"strength": 6, "strength_percent": .20, "agility": 8}, (("iron", 500), ("copper", 85), ("zinc", 70), ("tin", 55), ("oak", 80))),
        ("Меч Коготь Грифона", "i.weapon.13.12.griffon-claw-sword", 1150, 135, 80, 13, 7, 12, 55, 55, 55, 42, 50, .55, .35, {"strength": 5, "agility": 4, "luck": 4}, (("iron", 490), ("sulfur", 80), ("copper", 100), ("tin", 60), ("beech", 100))),
        ("Меч Небесных Паладинов", "i.weapon.13.12.heavenly-paladins-sword", 1180, 135, 80, 13, 7, 12, 60, 75, 0, 43, 48, .60, 0, {"strength": 8, "strength_percent": .25, "agility": 6}, (("iron", 470), ("copper", 90), ("zinc", 60), ("tin", 55), ("spruce", 25))),
    )
    return tuple(
        ProductionItem(name, slug, ItemType.WEAPON, "1.13.forge", price, weight, max_wear, stages, experience, level, requirements(level, strength, agility, luck, damage_min=damage_min, damage_max=damage_max, dodge_self=dodge, crit_self=crit, max_wear=max_wear), abilities, components=components)
        for name, slug, price, weight, max_wear, stages, experience, level, strength, agility, luck, damage_min, damage_max, dodge, crit, abilities, components in rows
    )


def _axes() -> tuple[ProductionItem, ...]:
    rows = (
        # Уровень 1
        ("Топор Стражника", "i.weapon.13.1.axe-guard", 17, 30, 20, None, None, 1, 0, 0, 0, 3, 7, 0, 0, None, ()),

        # Уровень 2
        ("Топор Месяца", "i.weapon.13.2.axe-moon", 55, 50, 30, None, None, 2, 12, 0, 0, 6, 10, 0, 0, {"strength_percent": .15}, ()),
        ("Стальной Топор", "i.weapon.13.2.axe-steel", 55, 50, 30, None, None, 2, 0, 0, 8, 6, 10, 0, .05, {"strength_percent": .10}, ()),
        ("Лесной Топор", "i.weapon.13.2.axe-forest", 55, 50, 30, None, None, 2, 0, 8, 0, 6, 10, .05, 0, {"strength_percent": .10}, ()),

        # Уровень 4
        ("Топор Крови", "i.weapon.13.4.axe-blood", 180, 85, 45, 5, 1, 4, 0, 0, 15, 14, 18, 0, .20, {"strength": 2, "strength_percent": .05, "luck": 1}, (("iron", 110), ("lead", 30), ("beech", 30))),
        ("Топор Легкости", "i.weapon.13.4.axe-lightness", 180, 85, 45, 5, 1, 4, 0, 15, 0, 14, 18, .15, 0, {"strength": 2, "strength_percent": .15, "agility": 1}, (("iron", 90), ("lead", 30), ("oak", 25))),
        ("Топор Резак", "i.weapon.13.4.axe-cutter", 180, 85, 45, 5, 1, 4, 20, 0, 0, 14, 18, 0, .10, {"strength": 2, "strength_percent": .15, "luck": 1}, (("iron", 110), ("lead", 25), ("birch", 25))),

        # Уровень 6
        ("Топор Каратель", "i.weapon.13.6.axe-punisher", 230, 105, 70, 7, 2, 6, 20, 0, 15, 19, 27, 0, .20, {"strength": 2, "strength_percent": .15, "luck": 3}, (("iron", 130), ("sulfur", 30), ("lead", 35))),
        ("Топор Страж Порядка", "i.weapon.13.6.axe-order-guardian", 230, 105, 70, 7, 2, 6, 25, 0, 0, 19, 27, 0, 0, {"strength": 3, "strength_percent": .25, "agility": 1, "luck": 1}, (("iron", 140), ("sulfur", 35), ("lead", 30))),
        ("Топор Стервятника", "i.weapon.13.6.axe-vulture", 230, 105, 70, 7, 2, 6, 20, 15, 0, 20, 27, .20, 0, {"strength": 2, "strength_percent": .15, "agility": 3}, (("iron", 115), ("sulfur", 35), ("lead", 35))),

        # Уровень 8
        ("Топор Зноя", "i.weapon.13.8.axe-heat", 440, 115, 80, 9, 3, 8, 40, 0, 40, 27, 34, 0, .20, {"strength": 5, "strength_percent": .20, "agility": 1, "luck": 1}, (("iron", 205), ("copper", 50), ("lead", 50), ("oak", 50))),
        ("Топор Холода", "i.weapon.13.8.axe-cold", 460, 115, 80, 9, 3, 8, 40, 40, 0, 28, 36, .20, 0, {"strength": 4, "strength_percent": .20, "agility": 2}, (("iron", 210), ("copper", 60), ("lead", 55), ("birch", 40))),

        # Уровень 10
        ("Топор Добрый Вестник", "i.weapon.13.10.axe-good-messenger", 730, 140, 80, 11, 5, 10, 60, 35, 45, 31, 40, 0, .30, {"strength": 4, "strength_percent": .25, "luck": 6}, (("iron", 290), ("silicon", 70), ("lead", 90), ("spruce", 30))),
        ("Топор Разделитель", "i.weapon.13.10.axe-divider", 750, 140, 80, 11, 5, 10, 45, 62, 0, 32, 42, .25, 0, {"strength": 4, "strength_percent": .30, "agility": 4, "luck": 2}, (("iron", 305), ("silicon", 80), ("lead", 70), ("mahogany", 20))),
        ("Топор Горлогрыз", "i.weapon.13.10.axe-throat-biter", 750, 140, 80, 11, 5, 10, 45, 0, 60, 32, 41, .15, .20, {"strength": 4, "strength_percent": .25, "agility": 3, "luck": 3}, (("iron", 335), ("silicon", 90), ("lead", 75), ("spruce", 30))),
        ("Топор Грань Безумия", "i.weapon.13.10.axe-edge-of-madness", 770, 140, 80, 11, 5, 10, 70, 40, 40, 33, 42, .20, .15, {"strength": 5, "strength_percent": .30, "agility": 1, "luck": 2}, (("iron", 300), ("silicon", 75), ("lead", 80), ("mahogany", 20))),

        # Уровень 12
        ("Топор Укротителя Драконов", "i.weapon.13.12.axe-dragon-tamer", 1200, 155, 85, 13, 7, 12, 85, 52, 0, 42, 49, .30, .10, {"strength": 7, "strength_percent": .35, "agility": 5, "luck": 2}, (("iron", 500), ("lead", 120), ("tin", 60), ("beech", 130))),
        ("Топор Кровавого Шамана", "i.weapon.13.12.axe-blood-shaman", 1150, 155, 85, 13, 7, 12, 55, 68, 0, 41, 49, .45, 0, {"strength": 7, "strength_percent": .35, "agility": 3, "luck": 4}, (("iron", 480), ("lead", 100), ("tin", 65), ("beech", 110))),
        ("Топор Мертвой Земли", "i.weapon.13.12.axe-dead-land", 1200, 155, 85, 13, 7, 12, 55, 0, 68, 41, 50, .10, .45, {"strength": 7, "strength_percent": .20, "agility": 4, "luck": 4}, (("iron", 550), ("lead", 90), ("tin", 70), ("beech", 100))),
        ("Топор Жреца Антапехта", "i.weapon.13.12.axe-priest-antapeht", 1150, 155, 85, 13, 7, 12, 65, 35, 52, 40, 49, .10, .50, {"strength": 7, "strength_percent": .10, "luck": 8}, (("iron", 540), ("lead", 115), ("tin", 60), ("beech", 115))),
    )
    return tuple(
        ProductionItem(name, slug, ItemType.WEAPON, "1.13.forge", price, weight, max_wear, stages, experience, level, requirements(level, strength, agility, luck, damage_min=damage_min, damage_max=damage_max, dodge_self=dodge, crit_self=crit, max_wear=max_wear), abilities, components=components)
        for name, slug, price, weight, max_wear, stages, experience, level, strength, agility, luck, damage_min, damage_max, dodge, crit, abilities, components in rows
    )


def _hammers() -> tuple[ProductionItem, ...]:
    rows = (
        # Уровень 1
        ("Дубинка Разбойника", "i.weapon.13.1.hammer-bandit-club", 16, 35, 20, None, None, 1, 0, 0, 0, 2, 8, 0, 0, None, ()),

        # Уровень 2
        ("Цеп Дробитель", "i.weapon.13.2.hammer-flail-crusher", 60, 60, 30, None, None, 2, 8, 0, 0, 5, 11, 0, .10, {"strength_percent": .05}, ()),
        ("Булава Воина", "i.weapon.13.2.hammer-warrior-mace", 60, 60, 30, None, None, 2, 0, 0, 11, 5, 11, 0, .15, None, ()),
        ("Цеп Друидов", "i.weapon.13.2.hammer-druid-flail", 60, 60, 30, None, None, 2, 0, 8, 0, 5, 11, .05, .10, None, ()),

        # Уровень 4
        ("Молот Искателя", "i.weapon.13.4.hammer-seeker", 200, 95, 45, 5, 1, 4, 0, 0, 15, 12, 20, .05, .20, {"luck": 3}, (("iron", 100), ("copper", 30), ("mica", 30))),
        ("Молот Миротворца", "i.weapon.13.4.hammer-peacemaker", 200, 95, 45, 5, 1, 4, 0, 0, 20, 12, 20, 0, .25, {"luck": 3}, (("iron", 115), ("copper", 25), ("mica", 30))),
        ("Молот Убийца", "i.weapon.13.4.hammer-killer", 200, 95, 45, 5, 1, 4, 15, 0, 0, 12, 20, 0, .15, {"strength": 1, "strength_percent": .15, "luck": 2}, (("iron", 95), ("copper", 25), ("mica", 35))),

        # Уровень 6
        ("Молот Разрушитель", "i.weapon.13.6.hammer-destroyer", 250, 120, 70, 7, 2, 6, 0, 0, 25, 18, 29, 0, .30, {"strength_percent": .05, "luck": 5}, (("iron", 120), ("copper", 35), ("mica", 35), ("oak", 10))),
        ("Молот Завоеватель", "i.weapon.13.6.hammer-conqueror", 250, 120, 70, 7, 2, 6, 25, 0, 0, 19, 28, 0, .25, {"strength": 1, "strength_percent": .10, "luck": 4}, (("iron", 130), ("copper", 30), ("mica", 35), ("birch", 10))),

        # Уровень 8
        ("Молот Светлых Сил", "i.weapon.13.8.hammer-light-forces", 450, 125, 80, 9, 3, 8, 35, 0, 45, 24, 37, .15, .30, {"strength": 2, "agility": 2, "luck": 3}, (("iron", 210), ("silicon", 50), ("mica", 70), ("beech", 50))),
        ("Молот Темных Сил", "i.weapon.13.8.hammer-dark-forces", 480, 125, 80, 9, 3, 8, 45, 0, 35, 25, 38, 0, .40, {"strength": 3, "strength_percent": .05, "luck": 3}, (("iron", 225), ("silicon", 70), ("mica", 65), ("beech", 50))),

        # Уровень 10
        ("Молот Выключатель", "i.weapon.13.10.hammer-switch-off", 720, 160, 75, 11, 5, 10, 50, 0, 50, 30, 43, 0, .45, {"strength": 4, "strength_percent": .25, "agility": 2, "luck": 3}, (("iron", 300), ("silicon", 80), ("mica", 100), ("oak", 80))),
        ("Молот Тяжелой Руки", "i.weapon.13.10.hammer-heavy-hand", 750, 160, 75, 11, 5, 10, 45, 0, 60, 30, 44, .10, .55, {"strength": 3, "agility": 2, "luck": 5}, (("iron", 370), ("silicon", 90), ("mica", 85), ("birch", 80))),
        ("Молот Внезапный Поцелуй", "i.weapon.13.10.hammer-sudden-kiss", 770, 160, 80, 11, 5, 10, 45, 0, 65, 31, 45, 0, .50, {"strength": 4, "strength_percent": .15, "luck": 6}, (("iron", 315), ("silicon", 80), ("mica", 85), ("spruce", 35))),

        # Уровень 12
        ("Молот Черепомол", "i.weapon.13.12.hammer-skull-grinder", 1200, 165, 80, 13, 7, 12, 60, 0, 80, 41, 51, .25, .55, {"strength": 7, "agility": 4, "luck": 3}, (("iron", 500), ("mica", 115), ("lead", 90), ("spruce", 50))),
        ("Молот Первобытного Страха", "i.weapon.13.12.hammer-primal-fear", 1250, 165, 80, 13, 7, 12, 65, 0, 75, 39, 53, 0, .65, {"strength": 5, "strength_percent": .15, "agility": 2, "luck": 7}, (("iron", 540), ("mica", 100), ("lead", 85), ("mahogany", 35))),
        ("Молот Рука Сваруда", "i.weapon.13.12.hammer-swarud-hand", 1150, 170, 85, 13, 7, 12, 70, 0, 55, 40, 52, 0, .55, {"strength": 6, "strength_percent": .25, "agility": 3, "luck": 5}, (("iron", 480), ("mica", 135), ("lead", 110), ("beech", 150))),
    )
    return tuple(
        ProductionItem(name, slug, ItemType.WEAPON, "1.13.forge", price, weight, max_wear, stages, experience, level, requirements(level, strength, agility, luck, damage_min=damage_min, damage_max=damage_max, dodge_self=dodge, crit_self=crit, max_wear=max_wear), abilities, components=components)
        for name, slug, price, weight, max_wear, stages, experience, level, strength, agility, luck, damage_min, damage_max, dodge, crit, abilities, components in rows
    )


# --- ПЛАЩИ (CLOAK) ---

def _cloaks() -> tuple[ProductionItem, ...]:
    tiers = (
        (6, "harmony", "Гармонии", 450, 40, 45, 2, 4, 13, {"health": 80, "mana": 25, "magic_order_1_self": 0.25}),
        (8, "wisdom", "Мудрости", 1200, 50, 55, 4, 8, 25, {"health": 100, "mana": 50, "magic_order_1_self": 0.35, "magic_order_2_self": 0.25}),
        (10, "power", "Силы", 2055, 60, 65, 8, 12, 40, {"health": 110, "mana": 75, "magic_order_1_self": 0.35, "magic_order_2_self": 0.30, "magic_order_3_self": 0.20}),
        (12, "eternity", "Вечности", 4110, 70, 75, 12, 16, 49, {"health": 120, "mana": 100, "magic_order_1_self": 0.40, "magic_order_2_self": 0.40, "magic_order_3_self": 0.40}),
    )
    affinities = (
        ("balance", "Равновесия"), ("order", "Порядка"), ("mind", "Разума"),
        ("chaos", "Хаоса"), ("feelings", "Чувств"), ("nature", "Природы"),
    )
    races = (
        (Race.ORC, "orc"),
        (Race.ELF, "elf"),
        (Race.HUMAN, "human"),
    )
    return tuple(
        ProductionItem(
            name=f"Плащ {title} {affinity_name}",
            slug=f"i.cloak.13.{level}.{race_slug}-{tier}-{affinity}-cloak",
            item_type=ItemType.CLOAK,
            location_slug="1.13.forge",
            price=price,
            weight=weight,
            max_wear=max_wear,
            craft_stages=None,
            craft_experience=None,
            minimal_level=level,
            parameters=requirements(level, affinity=affinity, damage_min=damage_min, damage_max=damage_max, defense=defense, max_wear=max_wear),
            ability_parameters=abilities,
            race=race,
        )
        for race, race_slug in races
        for level, tier, title, price, weight, max_wear, damage_min, damage_max, defense, abilities in tiers
        for affinity, affinity_name in affinities
    )

# --- БРОНЯ (HELMET/ARMOR/GAUNTLETS/GLOVES/LEGGINGS/BOOTS) ---

def _bronze_armor() -> tuple[ProductionItem, ...]:
    slots = (
        (ItemType.HELMET, "helmet", "Шлем", 25, 10, 20, 8, {"health": 10}),
        (ItemType.ARMOR, "armor", "Доспех", 40, 30, 30, 8, None),
        (ItemType.GAUNTLETS, "gauntlets", "Нарукавники", 15, 10, 20, 8, None),
        (ItemType.GLOVES, "gloves", "Перчатки", 10, 10, 15, None, None),
        (ItemType.LEGGINGS, "leggings", "Поножи", 15, 20, 25, 8, None),
        (ItemType.BOOTS, "boots", "Сандалии", 10, 10, 20, 8, None),
    )
    races = (
        (Race.ORC, "orc", "Орка", 12, 9, 9),
        (Race.ELF, "elf", "Эльфа", 9, 12, 9),
        (Race.HUMAN, "human", "Человека", 9, 9, 12),
    )

    armor_pieces = tuple(
        ProductionItem(
            name=f"{slot_name} Бронзового {race_name}",
            slug=f"i.{item_type.value}.13.4.{race_slug}-bronze-{slot_slug}",
            item_type=item_type,
            location_slug="1.13.forge",
            price=price,
            weight=weight,
            max_wear=max_wear,
            craft_stages=None,
            craft_experience=None,
            minimal_level=4,
            parameters=requirements(4, strength, agility, luck, max_wear=max_wear, **({"defense": defense} if defense else {"damage_min": 1, "damage_max": 2})),
            ability_parameters=abilities,
            race=race,
        )
        for race, race_slug, race_name, strength, agility, luck in races
        for item_type, slot_slug, slot_name, price, weight, max_wear, defense, abilities in slots
    )

    # Комплекты (Бронза, не крафтятся)
    kits = tuple(
        ProductionItem(
            name=f"Броня Бронзового {race_name} (Комплект)",
            slug=f"i.armor.13.4.{race_slug}-bronze-kit",
            item_type=ItemType.KIT,
            location_slug="1.13.forge",
            price=kit_price,
            weight=kit_weight,
            max_wear=0,
            craft_stages=None,
            craft_experience=None,
            minimal_level=4,
            parameters=requirements(4, str, agi, luck, max_wear=None, kit_items=[
                f"i.helmet.13.4.{race_slug}-bronze-helmet",
                f"i.armor.13.4.{race_slug}-bronze-armor",
                f"i.gauntlets.13.4.{race_slug}-bronze-gauntlets",
                f"i.gloves.13.4.{race_slug}-bronze-gloves",
                f"i.leggings.13.4.{race_slug}-bronze-leggings",
                f"i.boots.13.4.{race_slug}-bronze-boots",
            ]),
            ability_parameters=None,
            race=race,
            components=(),
        )
        for race, race_slug, race_name, kit_price, kit_weight, (str, agi, luck) in (
            (Race.ORC, "orc", "Орка", 115, 90, (12, 9, 9)),
            (Race.ELF, "elf", "Эльфа", 115, 90, (9, 12, 9)),
            (Race.HUMAN, "human", "Человека", 115, 90, (9, 9, 12)),
        )
    )

    return armor_pieces + kits


def _armor_level_six() -> tuple[ProductionItem, ...]:
    slots = (
        (ItemType.HELMET, "helmet", "Шлем", 60, 20, 40, 3, 3, {"defense": 16}, {"health": 20}),
        (ItemType.ARMOR, "armor", "Доспех", 120, 40, 50, 5, 4, {"defense": 16}, {"health": 30}),
        (ItemType.GAUNTLETS, "gauntlets", "Нарукавники", 40, 20, 40, 3, 3, {"defense": 16}, None),
        (ItemType.GLOVES, "gloves", "Перчатки", 20, 10, 30, 2, 2, {"damage_min": 2, "damage_max": 4}, None),
        (ItemType.LEGGINGS, "leggings", "Поножи", 35, 30, 60, 4, 3, {"defense": 16}, None),
        (ItemType.BOOTS, "boots", "Сандалии", 25, 20, 30, 2, 2, {"defense": 16}, None),
    )
    races = (
        (Race.ORC, "orc", "Орка", 25, 17, 17, (("iron", 25), ("silicon", 10), ("mica", 10)), (("iron", 35), ("sulfur", 20), ("copper", 20), ("zinc", 10)), (("iron", 20), ("sulfur", 8), ("silicon", 8)), (("iron", 15), ("copper", 4), ("silicon", 2)), (("iron", 20), ("copper", 5), ("zinc", 5)), (("iron", 15), ("sulfur", 4), ("mica", 3))),
        (Race.ELF, "elf", "Эльфа", 17, 25, 17, (("iron", 25), ("silicon", 12), ("mica", 9)), (("iron", 35), ("sulfur", 25), ("copper", 20), ("zinc", 7)), (("iron", 20), ("sulfur", 6), ("silicon", 10)), (("iron", 15), ("copper", 3), ("silicon", 3)), (("iron", 25), ("copper", 4), ("zinc", 4)), (("iron", 15), ("sulfur", 3), ("mica", 4))),
        (Race.HUMAN, "human", "Человека", 17, 17, 25, (("iron", 33), ("silicon", 10), ("mica", 8)), (("iron", 35), ("sulfur", 20), ("copper", 25), ("zinc", 7)), (("iron", 20), ("sulfur", 10), ("silicon", 6)), (("iron", 10), ("copper", 4), ("silicon", 4)), (("iron", 22), ("copper", 4), ("zinc", 5)), (("iron", 20), ("sulfur", 2), ("mica", 3))),
    )

    armor_pieces = tuple(
        ProductionItem(
            name=f"{slot_name} Серебряного {race_name}",
            slug=f"i.{item_type.value}.13.6.{race_slug}-silver-{slot_slug}",
            item_type=item_type, location_slug="1.13.forge", price=price, weight=weight, max_wear=max_wear,
            craft_stages=stages, craft_experience=experience, minimal_level=6,
            parameters=requirements(6, strength, agility, luck, max_wear=max_wear, **(combat | ({"dodge_reduction": -.15, "crit_reduction": -.15} if item_type == ItemType.ARMOR and race == Race.ORC else {"crit_reduction": -.30} if item_type == ItemType.ARMOR and race == Race.ELF else {"dodge_reduction": -.30} if item_type == ItemType.ARMOR else {}))),
            ability_parameters=abilities, race=race, components=resources,
        )
        for race, race_slug, race_name, strength, agility, luck, *resource_rows in races
        for slot_index, (item_type, slot_slug, slot_name, price, weight, max_wear, stages, experience, combat, abilities) in enumerate(slots)
        for resources in (resource_rows[slot_index],)
    )

    # Комплекты (Серебро)
    kits = tuple(
        ProductionItem(
            name=f"Броня Серебряного {race_name} (Комплект)",
            slug=f"i.armor.13.6.{race_slug}-silver-kit",
            item_type=ItemType.KIT,
            location_slug="1.13.forge",
            price=kit_price,
            weight=kit_weight,
            max_wear=0,
            craft_stages=kit_stages,
            craft_experience=kit_exp,
            minimal_level=6,
            parameters=requirements(6, str, agi, luck, max_wear=None, kit_items=[
                f"i.helmet.13.6.{race_slug}-silver-helmet",
                f"i.armor.13.6.{race_slug}-silver-armor",
                f"i.gauntlets.13.6.{race_slug}-silver-gauntlets",
                f"i.gloves.13.6.{race_slug}-silver-gloves",
                f"i.leggings.13.6.{race_slug}-silver-leggings",
                f"i.boots.13.6.{race_slug}-silver-boots",
            ]),
            ability_parameters=None,
            race=race,
            components=kit_components,
        )
        for race, race_slug, race_name, kit_price, kit_weight, (str, agi, luck), kit_stages, kit_exp, kit_components in (
            (Race.ORC, "orc", "Орка", 300, 140, (25, 17, 17), 13, 15, (("iron", 130), ("sulfur", 32), ("copper", 29), ("silicon", 20), ("mica", 13), ("zinc", 15))),
            (Race.ELF, "elf", "Эльфа", 300, 140, (17, 25, 17), 13, 15, (("iron", 135), ("sulfur", 34), ("copper", 27), ("silicon", 25), ("mica", 13), ("zinc", 11))),
            (Race.HUMAN, "human", "Человека", 300, 140, (17, 17, 25), 13, 15, (("iron", 140), ("sulfur", 32), ("copper", 33), ("silicon", 20), ("mica", 11), ("zinc", 12))),
        )
    )

    return armor_pieces + kits


def _armor_level_eight() -> tuple[ProductionItem, ...]:
    slots = (
        (ItemType.HELMET, "helmet", "Шлем", 150, 30, 50, 4, 4, {"defense": 30}, {"health": 30}),
        (ItemType.ARMOR, "armor", "Доспех", 300, 60, 60, 6, 5, {"defense": 30}, {"health": 45}),
        (ItemType.GAUNTLETS, "gauntlets", "Нарукавники", 100, 30, 50, 4, 4, {"defense": 30, "crit_reduction": -.05}, None),
        (ItemType.GLOVES, "gloves", "Перчатки", 50, 10, 50, 2, 2, {"damage_min": 4, "damage_max": 8}, None),
        (ItemType.LEGGINGS, "leggings", "Поножи", 130, 40, 70, 4, 4, {"defense": 30, "dodge_reduction": -.05}, None),
        (ItemType.BOOTS, "boots", "Сандалии", 70, 20, 40, 2, 2, {"defense": 30}, None),
    )
    races = (
        (Race.ORC, "orc", "Орка", 42, 30, 30, (("iron", 45), ("silicon", 25), ("mica", 25), ("topaz", 10)), (("iron", 60), ("sulfur", 35), ("copper", 45), ("zinc", 25), ("amethyst", 35)), (("iron", 35), ("sulfur", 15), ("silicon", 15), ("amethyst", 20)), (("iron", 20), ("copper", 11), ("silicon", 11)), (("iron", 40), ("copper", 20), ("zinc", 15), ("opal", 15)), (("iron", 25), ("sulfur", 15), ("mica", 10))),
        (Race.ELF, "elf", "Эльфа", 30, 42, 30, (("iron", 45), ("silicon", 22), ("mica", 22), ("topaz", 20)), (("iron", 60), ("sulfur", 40), ("copper", 40), ("zinc", 25), ("opal", 30)), (("iron", 35), ("sulfur", 10), ("silicon", 20), ("topaz", 22)), (("iron", 20), ("copper", 10), ("silicon", 12)), (("iron", 40), ("copper", 15), ("zinc", 15), ("amethyst", 25)), (("iron", 25), ("sulfur", 12), ("mica", 12))),
        (Race.HUMAN, "human", "Человека", 30, 30, 42, (("iron", 45), ("silicon", 20), ("mica", 20), ("opal", 20)), (("iron", 60), ("sulfur", 35), ("copper", 40), ("zinc", 25), ("topaz", 50)), (("iron", 35), ("sulfur", 20), ("silicon", 15), ("amethyst", 13)), (("iron", 20), ("copper", 12), ("silicon", 10)), (("iron", 40), ("copper", 15), ("zinc", 20), ("opal", 10)), (("iron", 25), ("sulfur", 10), ("mica", 14))),
    )

    # Основные слоты брони
    armor_pieces = tuple(
        ProductionItem(
            name=f"{slot_name} Золотого {race_name}",
            slug=f"i.{item_type.value}.13.8.{race_slug}-golden-{slot_slug}",
            item_type=item_type, location_slug="1.13.forge", price=price, weight=weight, max_wear=max_wear,
            craft_stages=stages, craft_experience=experience, minimal_level=8,
            parameters=requirements(8, strength, agility, luck, max_wear=max_wear, **(combat | ({"dodge_reduction": -.15, "crit_reduction": -.15} if item_type == ItemType.ARMOR and race == Race.ORC else {"crit_reduction": -.25} if item_type == ItemType.ARMOR and race == Race.ELF else {"dodge_reduction": -.25} if item_type == ItemType.ARMOR else {}))),
            ability_parameters=abilities, race=race, components=resources,
        )
        for race, race_slug, race_name, strength, agility, luck, *resource_rows in races
        for slot_index, (item_type, slot_slug, slot_name, price, weight, max_wear, stages, experience, combat, abilities) in enumerate(slots)
        for resources in (resource_rows[slot_index],)
    )

    # Комплекты (Золото, уровень 8)
    kits = tuple(
        ProductionItem(
            name=f"Броня Золотого {race_name} (Комплект)",
            slug=f"i.armor.13.8.{race_slug}-golden-kit",
            item_type=ItemType.KIT,
            location_slug="1.13.forge",
            price=kit_price,
            weight=kit_weight,
            max_wear=0,
            craft_stages=kit_stages,
            craft_experience=kit_exp,
            minimal_level=8,
            parameters=requirements(8, str, agi, luck, max_wear=None, kit_items=[
                f"i.helmet.13.8.{race_slug}-golden-helmet",
                f"i.armor.13.8.{race_slug}-golden-armor",
                f"i.gauntlets.13.8.{race_slug}-golden-gauntlets",
                f"i.gloves.13.8.{race_slug}-golden-gloves",
                f"i.leggings.13.8.{race_slug}-golden-leggings",
                f"i.boots.13.8.{race_slug}-golden-boots",
            ]),
            ability_parameters=None,
            race=race,
            components=kit_components,
        )
        for race, race_slug, race_name, kit_price, kit_weight, (str, agi, luck), kit_stages, kit_exp, kit_components in (
            (Race.ORC, "orc", "Орка", 800, 190, (42, 30, 30), 16, 18, (("iron", 225), ("sulfur", 65), ("copper", 76), ("silicon", 51), ("mica", 35), ("zinc", 40), ("topaz", 10), ("amethyst", 55), ("opal", 15))),
            (Race.ELF, "elf", "Эльфа", 800, 190, (30, 42, 30), 16, 18, (("iron", 225), ("sulfur", 62), ("copper", 65), ("silicon", 54), ("mica", 34), ("zinc", 40), ("topaz", 42), ("amethyst", 25), ("opal", 30))),
            (Race.HUMAN, "human", "Человека", 800, 190, (30, 30, 42), 16, 18, (("iron", 225), ("sulfur", 65), ("copper", 67), ("silicon", 45), ("mica", 34), ("zinc", 45), ("topaz", 50), ("amethyst", 13), ("opal", 30))),
        )
    )

    return armor_pieces + kits

def _armor_level_ten() -> tuple[ProductionItem, ...]:
    slots = (
        (ItemType.HELMET, "helmet", "Шлем", 250, 35, 60, 5, 5, {"defense": 45}, {"health": 40}),
        (ItemType.ARMOR, "armor", "Доспех", 520, 70, 80, 7, 7, {"defense": 45}, {"health": 40}),
        (ItemType.GAUNTLETS, "gauntlets", "Нарукавники", 180, 30, 70, 5, 5, {"defense": 45, "dodge_reduction": -.05, "crit_reduction": -.05}, None),
        (ItemType.GLOVES, "gloves", "Перчатки", 90, 15, 50, 3, 3, {"damage_min": 8, "damage_max": 12}, None),
        (ItemType.LEGGINGS, "leggings", "Поножи", 210, 45, 70, 5, 5, {"defense": 45, "dodge_reduction": -.05, "crit_reduction": -.05}, None),
        (ItemType.BOOTS, "boots", "Сандалии", 120, 20, 50, 3, 3, {"defense": 45}, None),
    )
    races = (
        (Race.ORC, "orc", "Орка", 65, 39, 39, (("iron",70),("sulfur",30),("silicon",30),("mica",25),("diamond",5)), (("iron",100),("copper",60),("silicon",45),("lead",30),("tin",15),("sapphire",35)), (("iron",55),("sulfur",20),("silicon",20),("zinc",10),("topaz",40)), (("iron",35),("copper",15),("mica",15)), (("iron",60),("copper",40),("zinc",15),("lead",15),("amethyst",10)), (("iron",35),("sulfur",25),("lead",15),("opal",10))),
        (Race.ELF, "elf", "Эльфа", 52, 52, 37, (("iron",70),("sulfur",40),("silicon",30),("mica",20),("diamond",5)), (("iron",100),("copper",55),("silicon",45),("lead",30),("tin",15),("ruby",30)), (("iron",55),("sulfur",20),("silicon",20),("zinc",15),("opal",20)), (("iron",35),("copper",20),("mica",10)), (("iron",60),("copper",40),("zinc",20),("lead",10),("topaz",15)), (("iron",35),("sulfur",20),("lead",15),("amethyst",15))),
        (Race.HUMAN, "human", "Человека", 52, 37, 52, (("iron",70),("sulfur",25),("silicon",35),("mica",25),("diamond",5)), (("iron",100),("copper",60),("silicon",40),("lead",30),("tin",15),("emerald",30)), (("iron",55),("sulfur",15),("silicon",15),("zinc",10),("amethyst",45)), (("iron",40),("copper",20),("mica",10)), (("iron",60),("copper",35),("zinc",15),("lead",15),("opal",14)), (("iron",35),("sulfur",20),("lead",10),("topaz",30))),
    )

    armor_pieces = tuple(
        ProductionItem(
            name=f"Мифриловые {slot_name} {race_name}" if item_type in {ItemType.GAUNTLETS, ItemType.GLOVES, ItemType.LEGGINGS, ItemType.BOOTS} else f"Мифриловый {slot_name} {race_name}",
            slug=f"i.{item_type.value}.13.10.{race_slug}-mithril-{slot_slug}",
            item_type=item_type, location_slug="1.13.forge", price=price, weight=weight, max_wear=max_wear,
            craft_stages=stages, craft_experience=experience, minimal_level=10,
            parameters=requirements(10, strength, agility, luck, max_wear=max_wear, **(combat | ({"dodge_reduction": -.25, "crit_reduction": -.25} if item_type == ItemType.ARMOR and race == Race.ORC else {"crit_reduction": -.55} if item_type == ItemType.ARMOR and race == Race.ELF else {"dodge_reduction": -.55} if item_type == ItemType.ARMOR else {}))),
            ability_parameters=abilities, race=race, components=resources,
        )
        for race, race_slug, race_name, strength, agility, luck, *resource_rows in races
        for slot_index, (item_type, slot_slug, slot_name, price, weight, max_wear, stages, experience, combat, abilities) in enumerate(slots)
        for resources in (resource_rows[slot_index],)
    )

    kits = tuple(
        ProductionItem(
            name=f"Мифриловая Броня {race_name} (Комплект)",
            slug=f"i.armor.13.10.{race_slug}-mithril-kit",
            item_type=ItemType.KIT,
            location_slug="1.13.forge",
            price=kit_price,
            weight=kit_weight,
            max_wear=0,
            craft_stages=kit_stages,
            craft_experience=kit_exp,
            minimal_level=10,
            parameters=requirements(10, str, agi, luck, max_wear=None, kit_items=[
                f"i.helmet.13.10.{race_slug}-mithril-helmet",
                f"i.armor.13.10.{race_slug}-mithril-armor",
                f"i.gauntlets.13.10.{race_slug}-mithril-gauntlets",
                f"i.gloves.13.10.{race_slug}-mithril-gloves",
                f"i.leggings.13.10.{race_slug}-mithril-leggings",
                f"i.boots.13.10.{race_slug}-mithril-boots",
            ]),
            ability_parameters=None,
            race=race,
            components=kit_components,
        )
        for race, race_slug, race_name, kit_price, kit_weight, (str, agi, luck), kit_stages, kit_exp, kit_components in (
            (Race.ORC, "orc", "Орка", 1370, 215, (65, 39, 39), 21, 25, (("iron", 355), ("sulfur", 75), ("copper", 115), ("silicon", 95), ("mica", 40), ("zinc", 25), ("lead", 60), ("tin", 15), ("topaz", 40), ("amethyst", 10), ("opal", 10), ("sapphire", 35), ("diamond", 5))),
            (Race.ELF, "elf", "Эльфа", 1370, 215, (52, 52, 37), 21, 25, (("iron", 355), ("sulfur", 80), ("copper", 115), ("silicon", 95), ("mica", 30), ("zinc", 35), ("lead", 55), ("tin", 15), ("topaz", 15), ("amethyst", 15), ("opal", 20), ("ruby", 30), ("diamond", 5))),
            (Race.HUMAN, "human", "Человека", 1370, 215, (52, 37, 52), 21, 25, (("iron", 360), ("sulfur", 60), ("copper", 115), ("silicon", 90), ("mica", 35), ("zinc", 25), ("lead", 55), ("tin", 15), ("topaz", 30), ("amethyst", 45), ("opal", 14), ("emerald", 30), ("diamond", 5))),
        )
    )

    return armor_pieces + kits

def _armor_level_twelve() -> tuple[ProductionItem, ...]:
    slots = (
        (ItemType.HELMET, "helmet", "Шлем", 500, 45, 70, 6, 6, {"defense": 55}, {"health": 50}),
        (ItemType.ARMOR, "armor", "Доспех", 1040, 75, 90, 9, 8, {"defense": 55}, {"health": 50}),
        (ItemType.GAUNTLETS, "gauntlets", "Нарукавники", 360, 40, 80, 6, 6, {"defense": 55, "dodge_reduction": -.10, "crit_reduction": -.10}, None),
        (ItemType.GLOVES, "gloves", "Перчатки", 180, 20, 60, 4, 4, {"damage_min": 12, "damage_max": 16}, None),
        (ItemType.LEGGINGS, "leggings", "Поножи", 420, 55, 80, 7, 6, {"defense": 55, "dodge_reduction": -.10, "crit_reduction": -.10}, None),
        (ItemType.BOOTS, "boots", "Сандалии", 240, 25, 60, 4, 4, {"defense": 55}, None),
    )
    races = (
        (Race.ORC, "orc", "Орка", 83, 42, 42, (("iron",150),("sulfur",70),("silicon",70),("mica",30),("amethyst",30),("sapphire",20)), (("iron",250),("copper",80),("silicon",60),("lead",50),("tin",30),("emerald",30),("diamond",25)), (("iron",115),("sulfur",45),("silicon",45),("zinc",25),("topaz",35),("amethyst",15)), (("iron",75),("copper",35),("mica",15),("opal",15)), (("iron",130),("copper",55),("zinc",30),("lead",25),("topaz",25),("ruby",17)), (("iron",90),("sulfur",35),("lead",20),("opal",20),("sapphire",15))),
        (Race.ELF, "elf", "Эльфа", 62, 62, 40, (("iron",150),("sulfur",65),("silicon",60),("mica",35),("opal",25),("sapphire",25)), (("iron",250),("copper",75),("silicon",65),("lead",50),("tin",30),("ruby",30),("diamond",25)), (("iron",115),("sulfur",50),("silicon",40),("zinc",20),("topaz",45),("amethyst",15)), (("iron",75),("copper",40),("mica",15),("topaz",15)), (("iron",130),("copper",55),("zinc",25),("lead",30),("opal",20),("sapphire",20)), (("iron",90),("sulfur",30),("lead",20),("amethyst",20),("emerald",15))),
        (Race.HUMAN, "human", "Человека", 62, 40, 62, (("iron",150),("sulfur",60),("silicon",60),("mica",35),("topaz",40),("emerald",20)), (("iron",250),("copper",70),("silicon",60),("lead",55),("tin",30),("sapphire",40),("diamond",25)), (("iron",115),("sulfur",45),("silicon",45),("zinc",30),("amethyst",25),("opal",10)), (("iron",85),("copper",35),("mica",15),("amethyst",15)), (("iron",130),("copper",60),("zinc",25),("lead",25),("opal",25),("ruby",15)), (("iron",75),("sulfur",35),("lead",25),("topaz",25),("sapphire",15))),
    )

    armor_pieces = tuple(
        ProductionItem(
            name=f"{slot_name} Темного {race_name}",
            slug=f"i.{item_type.value}.13.12.{race_slug}-dark-{slot_slug}",
            item_type=item_type, location_slug="1.13.forge", price=price, weight=weight, max_wear=max_wear,
            craft_stages=stages, craft_experience=experience, minimal_level=12,
            parameters=requirements(12, strength, agility, luck, max_wear=max_wear, **(combat | ({"dodge_reduction": -.35, "crit_reduction": -.35} if item_type == ItemType.ARMOR and race == Race.ORC else {"crit_reduction": -.70} if item_type == ItemType.ARMOR and race == Race.ELF else {"dodge_reduction": -.70} if item_type == ItemType.ARMOR else {}))),
            ability_parameters=abilities, race=race, components=resources,
        )
        for race, race_slug, race_name, strength, agility, luck, *resource_rows in races
        for slot_index, (item_type, slot_slug, slot_name, price, weight, max_wear, stages, experience, combat, abilities) in enumerate(slots)
        for resources in (resource_rows[slot_index],)
    )

    kits = tuple(
        ProductionItem(
            name=f"Броня Темного {race_name} (Комплект)",
            slug=f"i.armor.13.12.{race_slug}-dark-kit",
            item_type=ItemType.KIT,
            location_slug="1.13.forge",
            price=kit_price,
            weight=kit_weight,
            max_wear=0,
            craft_stages=kit_stages,
            craft_experience=kit_exp,
            minimal_level=12,
            parameters=requirements(12, str, agi, luck, max_wear=None, kit_items=[
                f"i.helmet.13.12.{race_slug}-dark-helmet",
                f"i.armor.13.12.{race_slug}-dark-armor",
                f"i.gauntlets.13.12.{race_slug}-dark-gauntlets",
                f"i.gloves.13.12.{race_slug}-dark-gloves",
                f"i.leggings.13.12.{race_slug}-dark-leggings",
                f"i.boots.13.12.{race_slug}-dark-boots",
            ]),
            ability_parameters=None,
            race=race,
            components=kit_components,
        )
        for race, race_slug, race_name, kit_price, kit_weight, (str, agi, luck), kit_stages, kit_exp, kit_components in (
            (Race.ORC, "orc", "Орка", 2740, 260, (83, 42, 42), 30, 30, (("iron", 810), ("sulfur", 150), ("copper", 170), ("silicon", 175), ("mica", 45), ("zinc", 55), ("lead", 95), ("tin", 30), ("topaz", 60), ("amethyst", 45), ("opal", 35), ("sapphire", 35), ("emerald", 30), ("ruby", 17), ("diamond", 25))),
            (Race.ELF, "elf", "Эльфа", 2740, 260, (62, 62, 40), 30, 30, (("iron", 810), ("sulfur", 145), ("copper", 170), ("silicon", 165), ("mica", 50), ("zinc", 45), ("lead", 100), ("tin", 30), ("topaz", 60), ("amethyst", 35), ("opal", 45), ("sapphire", 45), ("emerald", 15), ("ruby", 30), ("diamond", 25))),
            (Race.HUMAN, "human", "Человека", 2740, 260, (62, 40, 62), 30, 30, (("iron", 805), ("sulfur", 140), ("copper", 165), ("silicon", 165), ("mica", 50), ("zinc", 55), ("lead", 105), ("tin", 30), ("topaz", 65), ("amethyst", 40), ("opal", 35), ("sapphire", 55), ("emerald", 20), ("ruby", 15), ("diamond", 25))),
        )
    )

    return armor_pieces + kits

# =============================================================================
# ЮВЕЛИРНАЯ (1.16.jewelers)
# =============================================================================

# --- АМУЛЕТЫ (AMULET) ---

def _amulets() -> tuple[ProductionItem, ...]:
    rows = (
        # Уровень 3
        ("Амулет Везения", "luck-amulet", 15, 10, 10, 3, 2, 3, 0, 8, 0, {"crit_self": .20}, {"luck": 1}, (("topaz", 5), ("amethyst", 6))),
        ("Амулет Прыжка", "jump-amulet", 15, 10, 10, 3, 2, 3, 8, 0, 0, {"dodge_self": .20}, {"agility": 1}, (("topaz", 6), ("opal", 4))),
        ("Амулет Древесной Силы", "tree-strength-amulet", 15, 10, 10, 3, 2, 3, 0, 0, 8, {}, {"strength": 1, "strength_percent": .20}, (("amethyst", 6), ("opal", 4))),

        # Уровень 4
        ("Амулет Ветра", "wind-amulet", 20, 10, 15, 4, 3, 4, 0, 0, 12, {"crit_self": .30}, {"agility": 1}, (("topaz", 10), ("ruby", 3))),
        ("Амулет Акробата", "acrobat-amulet", 20, 10, 15, 4, 3, 4, 0, 12, 0, {"dodge_self": .30}, {"strength": 1}, (("amethyst", 8), ("emerald", 3))),
        ("Амулет Грубой Удачи", "rough-luck-amulet", 20, 10, 15, 4, 3, 4, 12, 0, 0, {}, {"strength_percent": .30, "luck": 1}, (("opal", 8), ("sapphire", 3))),

        # Уровень 5
        ("Амулет Звериной Атаки", "beast-attack-amulet", 35, 20, 20, 5, 4, 5, 15, 0, 15, {"defense": 1, "crit_self": .25}, {"strength": 2, "strength_percent": .25}, (("topaz", 14), ("ruby", 6))),
        ("Амулет Удачной Атаки", "lucky-attack-amulet", 35, 20, 20, 5, 4, 5, 0, 0, 20, {"defense": 1, "crit_self": .30}, {"agility": 1, "luck": 1, "strength_percent": .20}, (("amethyst", 9), ("opal", 9))),
        ("Амулет Стабильной Атаки", "stable-attack-amulet", 35, 20, 20, 5, 4, 5, 0, 15, 15, {"defense": 1, "dodge_self": .25, "crit_self": .25}, {"agility": 2}, (("opal", 9), ("sapphire", 6))),
        ("Амулет Искусства", "art-amulet", 35, 20, 20, 5, 4, 5, 0, 20, 0, {"defense": 1, "dodge_self": .30, "crit_self": .20}, {"luck": 2}, (("topaz", 13), ("opal", 8))),
        ("Амулет Точного Удара", "precision-strike-amulet", 35, 20, 20, 5, 4, 5, 20, 0, 0, {"defense": 1, "dodge_self": .20}, {"health": 10, "strength": 1, "strength_percent": .30, "agility": 1}, (("amethyst", 10), ("emerald", 7))),
        ("Амулет Горных Гномов", "mountain-dwarves-amulet", 35, 20, 20, 5, 4, 5, 15, 15, 0, {"defense": 1, "dodge_self": .30}, {"strength": 1, "strength_percent": .20, "luck": 1}, (("topaz", 13), ("amethyst", 10))),

        # Уровень 6
        ("Амулет Исполина", "giant-amulet", 50, 20, 25, 6, 5, 6, 18, 0, 14, {"defense": 3, "dodge_self": .40, "crit_self": .20}, {"health": 30, "strength_percent": .20}, (("amethyst", 13), ("ruby", 10))),
        ("Амулет Видения Цели", "target-vision-amulet", 50, 20, 25, 6, 5, 6, 18, 14, 0, {"defense": 2, "dodge_self": .30, "crit_self": .40}, {"health": 20, "strength_percent": .20}, (("opal", 15), ("emerald", 8))),
        ("Амулет Равнодействия", "equilibrium-amulet", 60, 20, 25, 6, 5, 6, 15, 15, 15, {"defense": 1, "dodge_self": .50, "crit_self": .50}, {"strength": 1, "agility": 1, "luck": 1}, (("topaz", 20), ("diamond", 5))),

        # Уровень 7
        ("Амулет Разрушения", "destruction-amulet", 100, 20, 25, 7, 5, 7, 0, 30, 35, {"defense": 2, "dodge_self": .30, "crit_self": .50}, {"health": 30, "strength_percent": .25}, (("amethyst", 25), ("emerald", 15), ("silicon", 11))),
        ("Амулет Свободы", "freedom-amulet", 100, 20, 25, 7, 5, 7, 0, 35, 30, {"defense": 3, "dodge_self": .50, "crit_self": .25}, {"health": 40, "strength_percent": .25}, (("opal", 20), ("ruby", 15), ("sulfur", 11))),
        ("Амулет Волка", "wolf-amulet", 110, 20, 25, 7, 5, 7, 35, 0, 0, {"defense": 1, "dodge_self": .55, "crit_self": .55}, {"strength": 1, "agility": 1, "luck": 1}, (("topaz", 30), ("sapphire", 20), ("mica", 10))),

        # Уровень 8
        ("Амулет Левитации", "levitation-amulet", 150, 20, 25, 8, 5, 8, 42, 0, 0, {"defense": 1, "dodge_self": .60, "crit_self": .60}, {"strength": 1, "agility": 1, "luck": 1}, (("topaz", 40), ("sapphire", 20), ("zinc", 20))),
        ("Амулет Отца Гор", "father-of-mountains-amulet", 140, 20, 25, 8, 5, 8, 0, 40, 30, {"defense": 3, "dodge_self": .50, "crit_self": .30}, {"health": 50, "strength_percent": .25}, (("amethyst", 35), ("sapphire", 15), ("lead", 20))),
        ("Амулет Наследника", "heir-amulet", 140, 20, 25, 8, 5, 8, 0, 30, 40, {"defense": 2, "dodge_self": .30, "crit_self": .60}, {"health": 35, "strength_percent": .25}, (("opal", 35), ("sapphire", 20), ("copper", 20))),

        # Уровень 9
        ("Амулет Крестоносца", "crusader-amulet", 240, 30, 30, 9, 6, 9, 52, 37, 37, {"defense": 1, "dodge_self": .70, "crit_self": .70}, {"strength": 1, "agility": 1, "luck": 1}, (("topaz", 50), ("amethyst", 45), ("ruby", 20), ("mica", 20))),
        ("Амулет Тайны Теней", "shadow-secrets-amulet", 220, 25, 30, 9, 6, 9, 52, 45, 32, {"defense": 1, "dodge_self": .70, "crit_self": .15}, {"health": 20, "strength_percent": .25}, (("amethyst", 50), ("sapphire", 25), ("emerald", 20), ("sulfur", 18))),
        ("Амулет Викинга", "viking-amulet", 260, 30, 30, 9, 6, 9, 62, 0, 0, {"defense": 1, "dodge_self": .30, "crit_self": .30}, {"health": 120, "strength_percent": .35, "agility": 1, "luck": 1}, (("topaz", 50), ("opal", 40), ("diamond", 10), ("lead", 20))),
        ("Амулет Кентавра", "centaur-amulet", 240, 30, 30, 9, 6, 9, 72, 0, 0, {"defense": 1}, {"health": 20, "strength_percent": .50}, (("amethyst", 50), ("opal", 45), ("emerald", 20), ("zinc", 10))),
        ("Амулет Дыхания Зевса", "zeus-breath-amulet", 220, 25, 30, 9, 6, 9, 52, 32, 45, {"defense": 1, "dodge_self": .30, "crit_self": .70}, {"health": 70, "strength_percent": .15}, (("topaz", 50), ("opal", 40), ("ruby", 20), ("silicon", 15))),

        # Уровень 10
        ("Амулет Рубиновое Сердце", "ruby-heart-amulet", 270, 25, 30, 9, 6, 10, 55, 48, 32, {"dodge_self": .75, "crit_self": .20}, {"health": 25, "strength_percent": .30}, (("amethyst", 50), ("opal", 40), ("ruby", 35), ("silicon", 10))),
        ("Амулет Глаз Смотрящего", "beholder-eye-amulet", 280, 25, 30, 9, 6, 10, 55, 32, 48, {"dodge_self": .35, "crit_self": .75}, {"health": 80, "strength_percent": .20}, (("topaz", 60), ("opal", 50), ("sapphire", 35), ("sulfur", 24))),
        ("Амулет Эйфории", "euphoria-amulet", 310, 35, 30, 9, 6, 10, 57, 38, 38, {"dodge_self": .75, "crit_self": .75}, {"strength": 1, "agility": 1, "luck": 1}, (("topaz", 60), ("amethyst", 55), ("emerald", 35), ("copper", 28))),
        ("Амулет Варвара", "barbarian-amulet", 320, 35, 30, 9, 6, 10, 80, 0, 0, {}, {"health": 75, "strength_percent": .55, "agility": 1, "luck": 1}, (("topaz", 70), ("amethyst", 65), ("opal", 60), ("zinc", 12))),

        # Уровень 11
        ("Амулет Мести", "vengeance-amulet", 350, 30, 30, 10, 7, 11, 58, 33, 52, {"dodge_self": .40, "crit_self": .80}, {"health": 90, "strength_percent": .30, "agility": 1}, (("topaz", 75), ("sapphire", 35), ("emerald", 35), ("silicon", 25), ("mica", 10))),
        ("Амулет Саламандры", "salamander-amulet", 340, 30, 30, 10, 7, 11, 58, 52, 33, {"dodge_self": .85, "crit_self": .25}, {"health": 40, "strength_percent": .35, "luck": 1}, (("amethyst", 65), ("sapphire", 35), ("ruby", 35), ("sulfur", 18), ("silicon", 10))),
        ("Амулет Печали", "sorrow-amulet", 400, 40, 30, 10, 7, 11, 60, 40, 40, {"dodge_self": .85, "crit_self": .85}, {"strength": 2, "agility": 1, "luck": 1}, (("topaz", 70), ("opal", 55), ("diamond", 20), ("sulfur", 25), ("lead", 10))),
        ("Амулет Роковой Ошибки", "fatal-mistake-amulet", 430, 45, 30, 10, 7, 11, 90, 0, 0, {}, {"health": 75, "strength_percent": .60, "agility": 2, "luck": 2}, (("amethyst", 65), ("opal", 60), ("diamond", 25), ("copper", 18), ("zinc", 10))),

        # Уровень 12
        ("Амулет Пронзающего Удара", "piercing-strike-amulet", 500, 35, 35, 10, 7, 12, 60, 35, 55, {"dodge_self": .40, "crit_self": .90}, {"health": 105, "strength": 1, "strength_percent": .30, "agility": 1}, (("topaz", 80), ("amethyst", 70), ("ruby", 35), ("diamond", 15), ("sulfur", 20), ("copper", 15))),
        ("Амулет Обмана", "deception-amulet", 490, 35, 35, 10, 7, 12, 60, 55, 35, {"dodge_self": .95, "crit_self": .30}, {"health": 45, "strength": 1, "strength_percent": .35, "agility": 1, "luck": 1}, (("amethyst", 70), ("opal", 55), ("ruby", 35), ("diamond", 10), ("copper", 25), ("zinc", 15))),
        ("Амулет Баланса", "balance-amulet", 510, 45, 35, 10, 7, 12, 63, 42, 42, {"dodge_self": .90, "crit_self": .90}, {"health": 10, "strength": 3, "agility": 1, "luck": 1}, (("topaz", 85), ("opal", 60), ("sapphire", 40), ("emerald", 35), ("silicon", 25), ("mica", 20))),
        ("Амулет Бессмертия", "immortality-amulet", 550, 50, 35, 10, 7, 12, 95, 0, 0, {}, {"health": 90, "strength_percent": .65, "agility": 2, "luck": 2}, (("topaz", 100), ("amethyst", 75), ("sapphire", 40), ("emerald", 35), ("sulfur", 30), ("tin", 10))),
        ("Амулет Охотника", "hunter-amulet", 530, 40, 35, 10, 7, 12, 105, 0, 0, {"dodge_self": .10, "crit_self": .10}, {"health": 20, "strength_percent": .85}, (("opal", 65), ("sapphire", 40), ("emerald", 35), ("ruby", 35), ("silicon", 30), ("lead", 20))),
    )
    return tuple(
        ProductionItem(name, f"i.amulet.16.{level}.{slug}", ItemType.AMULET, "1.16.jewelers", price, weight, max_wear, stages, experience, level, requirements(level, strength, agility, luck, max_wear=max_wear, **combat), abilities, components=components)
        for name, slug, price, weight, max_wear, stages, experience, level, strength, agility, luck, combat, abilities, components in rows
    )


# --- КУЛОНЫ (PENDANT) ---

def _pendants() -> tuple[ProductionItem, ...]:
    rows = (
        # Уровень 3
        ("Кулон Звериной Защиты", "beast-defense", 15, 10, 10, 3, 2, 3, 8, 0, 0, {"dodge_reduction": -.05, "crit_reduction": -.10}, {"health": 5}, (("opal", 9),)),
        ("Кулон Доблести", "valor", 15, 10, 10, 3, 2, 3, 0, 0, 8, {"dodge_reduction": -.15}, {"health": 5}, (("topaz", 2), ("amethyst", 9))),
        ("Кулон Твердости", "hardness", 15, 10, 10, 3, 2, 3, 0, 8, 0, {"crit_reduction": -.15}, {"health": 5}, (("topaz", 9), ("amethyst", 3))),

        # Уровень 4
        ("Кулон Крепкого Духа", "strong-spirit", 20, 20, 15, 4, 3, 4, 13, 0, 8, {"defense": 2, "dodge_reduction": -.10}, {"health": 20}, (("sapphire", 9),)),
        ("Кулон Стойкости", "perseverance", 20, 20, 15, 4, 3, 4, 10, 10, 0, {"defense": 1, "crit_reduction": -.20}, {"health": 10}, (("topaz", 2), ("opal", 10))),
        ("Кулон Здорового Духа", "healthy-spirit", 20, 20, 15, 4, 3, 4, 0, 10, 10, {"defense": 1, "dodge_reduction": -.05, "crit_reduction": -.05}, {"health": 20}, (("topaz", 12), ("amethyst", 4))),
        ("Кулон Прямоты", "straightness", 20, 20, 15, 4, 3, 4, 10, 0, 10, {"defense": 1, "dodge_reduction": -.20}, {"health": 10}, (("amethyst", 10), ("opal", 3))),

        # Уровень 5
        ("Кулон Лесной Защиты", "forest-protection", 30, 20, 15, 5, 4, 5, 0, 18, 0, {"defense": 1, "dodge_reduction": -.05, "crit_reduction": -.25}, {"health": 15}, (("amethyst", 15), ("emerald", 3))),
        ("Кулон Свирепого Зверя", "ferocious-beast", 30, 20, 15, 5, 4, 5, 18, 0, 0, {"defense": 1, "dodge_reduction": -.10, "crit_reduction": -.20}, {"health": 15}, (("opal", 12), ("ruby", 3))),
        ("Кулон Подвига", "feat", 30, 20, 15, 5, 4, 5, 0, 0, 18, {"defense": 1, "dodge_reduction": -.25, "crit_reduction": -.05}, {"health": 15}, (("topaz", 25),)),

        # Уровень 6
        ("Кулон Внимательности", "attentiveness", 45, 30, 20, 6, 5, 6, 0, 20, 0, {"defense": 1, "dodge_reduction": -.15, "crit_reduction": -.25}, {"health": 20}, (("topaz", 28), ("sapphire", 5))),
        ("Кулон Царя Зверей", "king-of-beasts", 45, 30, 20, 6, 5, 6, 20, 0, 0, {"defense": 1, "dodge_reduction": -.20, "crit_reduction": -.20}, {"health": 25}, (("amethyst", 23), ("sapphire", 5))),
        ("Кулон Героя", "hero", 45, 30, 20, 6, 5, 6, 0, 0, 20, {"defense": 1, "dodge_reduction": -.25, "crit_reduction": -.15}, {"health": 20}, (("opal", 19), ("sapphire", 5))),
        ("Кулон Громилы", "thug", 50, 30, 20, 6, 5, 6, 17, 15, 13, {"defense": 2, "dodge_reduction": -.15, "crit_reduction": -.15}, {"health": 40}, (("opal", 7), ("diamond", 5))),
        ("Кулон Выносливости", "endurance", 55, 30, 20, 6, 5, 6, 20, 20, 20, {"defense": 3, "dodge_reduction": -.15, "crit_reduction": -.15}, {"health": 20}, (("amethyst", 12), ("diamond", 5))),

        # Уровень 7
        ("Кулон Слез", "tears", 115, 30, 25, 7, 5, 7, 25, 25, 25, {"defense": 3, "dodge_reduction": -.25, "crit_reduction": -.25}, {"health": 20}, (("topaz", 43), ("amethyst", 43))),
        ("Кулон Жесткости", "rigidity", 110, 30, 25, 7, 5, 7, 35, 0, 30, {"defense": 1, "dodge_self": .05, "dodge_reduction": -.15, "crit_self": .20, "crit_reduction": -.20}, {"health": 40}, (("amethyst", 40), ("opal", 29))),
        ("Кулон Легкости", "lightness", 110, 30, 25, 7, 5, 7, 35, 30, 0, {"defense": 1, "dodge_self": .20, "dodge_reduction": -.20, "crit_self": .05, "crit_reduction": -.15}, {"health": 40}, (("topaz", 45), ("opal", 31))),

        # Уровень 8
        ("Кулон Отца Гор", "father-of-mountains", 155, 30, 25, 8, 5, 8, 42, 35, 0, {"defense": 2, "dodge_self": .30, "dodge_reduction": -.20, "crit_self": .05, "crit_reduction": -.20}, {"health": 50}, (("amethyst", 46), ("ruby", 28))),
        ("Кулон Сопротивления", "resistance", 155, 30, 25, 8, 5, 8, 42, 0, 35, {"defense": 1, "dodge_self": .10, "dodge_reduction": -.20, "crit_self": .30, "crit_reduction": -.20}, {"health": 60}, (("opal", 44), ("emerald", 25))),
        ("Кулон Круговой Обороны", "circular-defense", 165, 30, 25, 8, 5, 8, 35, 35, 35, {"defense": 3, "dodge_reduction": -.35, "crit_reduction": -.35}, {"health": 20}, (("topaz", 50), ("sapphire", 46))),

        # Уровень 9
        ("Кулон Слепящей Молнии", "blinding-lightning", 240, 35, 30, 9, 6, 9, 52, 45, 32, {"defense": 3, "dodge_self": .35, "dodge_reduction": -.30, "crit_self": .05, "crit_reduction": -.25}, {"health": 50}, (("topaz", 60), ("emerald", 20), ("diamond", 14))),
        ("Кулон Силы Вселенной", "universe-power", 250, 35, 30, 9, 6, 9, 60, 32, 32, {"defense": 4, "dodge_self": .05, "dodge_reduction": -.40, "crit_self": .05, "crit_reduction": -.40}, {"health": 25}, (("amethyst", 50), ("opal", 40), ("diamond", 14))),
        ("Кулон Крови Богов", "blood-of-gods", 240, 35, 30, 9, 6, 9, 52, 32, 45, {"defense": 2, "dodge_self": .10, "dodge_reduction": -.25, "crit_self": .30, "crit_reduction": -.30}, {"health": 80}, (("topaz", 60), ("ruby", 20), ("diamond", 14))),

        # Уровень 10
        ("Кулон Капля Крови", "drop-of-blood", 290, 35, 30, 9, 6, 10, 55, 48, 32, {"defense": 3, "dodge_self": .50, "dodge_reduction": -.25, "crit_reduction": -.35}, {"health": 60}, (("amethyst", 60), ("opal", 55), ("emerald", 33))),
        ("Кулон Сердце Голема", "golem-heart", 300, 35, 30, 9, 6, 10, 65, 33, 33, {"defense": 4, "dodge_self": .05, "dodge_reduction": -.45, "crit_self": .05, "crit_reduction": -.45}, {"health": 30}, (("amethyst", 70), ("opal", 65), ("sapphire", 36))),
        ("Кулон Ангела Молнии", "lightning-angel", 290, 35, 30, 9, 6, 10, 55, 32, 48, {"defense": 2, "dodge_reduction": -.35, "crit_self": .45, "crit_reduction": -.25}, {"health": 90}, (("amethyst", 60), ("opal", 55), ("ruby", 33))),

        # Уровень 11
        ("Кулон Проповедника", "preacher", 435, 40, 30, 10, 7, 11, 58, 52, 33, {"defense": 4, "dodge_self": .60, "dodge_reduction": -.35, "crit_reduction": -.40}, {"health": 65}, (("topaz", 90), ("amethyst", 75), ("sapphire", 55), ("sulfur", 55))),
        ("Кулон Печать Хаоса", "seal-of-chaos", 435, 40, 30, 10, 7, 11, 58, 33, 52, {"defense": 3, "dodge_reduction": -.45, "crit_self": .55, "crit_reduction": -.35}, {"health": 100}, (("topaz", 90), ("amethyst", 80), ("opal", 70), ("copper", 47))),
        ("Кулон Эволюции", "evolution", 450, 40, 30, 10, 7, 11, 70, 35, 35, {"defense": 5, "dodge_self": .05, "dodge_reduction": -.50, "crit_self": .05, "crit_reduction": -.55}, {"health": 50}, (("topaz", 90), ("opal", 70), ("sapphire", 55), ("silicon", 55))),

        # Уровень 12
        ("Кулон Озарения", "insight", 580, 40, 35, 10, 7, 12, 60, 55, 35, {"defense": 5, "dodge_self": .70, "dodge_reduction": -.40, "crit_reduction": -.50}, {"health": 70}, (("amethyst", 100), ("opal", 85), ("emerald", 55), ("mica", 43))),
        ("Кулон Возмездия", "retribution", 585, 40, 35, 10, 7, 12, 60, 35, 55, {"defense": 4, "dodge_reduction": -.55, "crit_self": .65, "crit_reduction": -.40}, {"health": 105}, (("amethyst", 100), ("opal", 85), ("ruby", 55), ("lead", 43))),
        ("Кулон Спокойствия", "tranquility", 570, 40, 35, 10, 7, 12, 75, 37, 37, {"defense": 6, "dodge_self": .10, "dodge_reduction": -.60, "crit_self": .10, "crit_reduction": -.60}, {"health": 60}, (("topaz", 100), ("sapphire", 60), ("diamond", 25), ("zinc", 45))),
        ("Кулон Вечности", "eternity", 610, 40, 35, 10, 7, 12, 60, 45, 45, {"defense": 4, "dodge_self": .25, "dodge_reduction": -.30, "crit_self": .25, "crit_reduction": -.20}, {"health": 150}, (("topaz", 120), ("amethyst", 105), ("opal", 90), ("tin", 21))),
    )
    return tuple(
        ProductionItem(name, f"i.pendant.16.{level}.{slug}", ItemType.PENDANT, "1.16.jewelers", price, weight, max_wear, stages, experience, level, requirements(level, strength, agility, luck, max_wear=max_wear, **combat), abilities, components=components)
        for name, slug, price, weight, max_wear, stages, experience, level, strength, agility, luck, combat, abilities, components in rows
    )


# --- КОЛЬЦА (RING) ---

def _rings() -> tuple[ProductionItem, ...]:
    rows = (
        # Уровень 2
        ("Кольцо Нерушимой Атаки", "unbreakable-attack", 15, 10, 10, 3, 2, 2, 6, 0, 0, {"dodge_reduction": -.05, "crit_reduction": -.05}, {"health": 6, "strength": 1}, (("topaz", 4), ("amethyst", 3), ("opal", 3))),
        ("Кольцо Кровавой Атаки", "bloody-attack", 15, 10, 10, 3, 2, 2, 0, 0, 6, {"dodge_reduction": -.05}, {"health": 6, "strength_percent": .05, "luck": 1}, (("topaz", 3), ("amethyst", 4), ("opal", 3))),
        ("Кольцо Быстрой Атаки", "fast-attack", 15, 10, 10, 3, 2, 2, 0, 6, 0, {"crit_reduction": -.05}, {"health": 6, "strength_percent": .05, "agility": 1}, (("topaz", 3), ("amethyst", 3), ("opal", 4))),

        # Уровень 3
        ("Кольцо Удачи", "luck-ring", 20, 10, 15, 4, 3, 3, 0, 0, 12, {"defense": 1, "crit_self": .10}, {"luck": 1}, (("topaz", 5), ("amethyst", 5), ("sapphire", 3))),
        ("Кольцо Удара", "strike-ring", 20, 10, 15, 4, 3, 3, 12, 0, 0, {"defense": 1}, {"strength": 1, "strength_percent": .10}, (("amethyst", 5), ("opal", 5), ("sapphire", 3))),
        ("Кольцо Реакции", "reaction-ring", 20, 10, 15, 4, 3, 3, 0, 12, 0, {"defense": 1, "dodge_self": .10}, {"agility": 1}, (("topaz", 5), ("opal", 5), ("sapphire", 3))),
        ("Кольцо Берсерка", "berserker-ring", 30, 10, 15, 4, 3, 3, 10, 0, 10, {"crit_self": .15}, {"strength_percent": .15}, (("topaz", 5), ("amethyst", 5), ("emerald", 5))),
        ("Кольцо Противостояния", "confrontation-ring", 30, 10, 15, 4, 3, 3, 0, 10, 10, {"defense": 1, "dodge_self": .05, "dodge_reduction": -.10, "crit_self": .05, "crit_reduction": -.10}, None, (("topaz", 5), ("amethyst", 5), ("ruby", 5))),

        # Уровень 4
        ("Кольцо Истинного Здоровья", "true-health-ring", 50, 10, 20, 5, 4, 4, 18, 0, 0, {"defense": 1, "dodge_reduction": -.05, "crit_reduction": -.05}, {"health": 30, "strength": 1}, (("topaz", 10), ("diamond", 4), ("sulfur", 8))),
        ("Кольцо Славного Здравия", "glorious-health-ring", 50, 10, 20, 5, 4, 4, 0, 0, 18, {"defense": 1, "dodge_reduction": -.05, "crit_self": .05}, {"health": 25, "strength_percent": .10, "luck": 1}, (("amethyst", 10), ("emerald", 6), ("lead", 6))),
        ("Кольцо Эфемерного Здоровья", "ephemeral-health-ring", 50, 10, 20, 5, 4, 4, 0, 18, 0, {"defense": 1, "dodge_self": .05, "crit_reduction": -.05}, {"health": 25, "strength_percent": .10, "agility": 1}, (("opal", 10), ("ruby", 6), ("silicon", 6))),

        # Уровень 5
        ("Кольцо Иммунитета", "immunity-ring", 80, 10, 25, 6, 5, 5, 20, 0, 0, {"defense": 2, "dodge_reduction": -.30, "crit_reduction": -.30}, {"health": 15, "strength_percent": .15, "agility": 1, "luck": 2}, (("topaz", 25), ("sapphire", 15), ("sulfur", 10))),
        ("Кольцо Славы", "glory-ring", 80, 10, 25, 6, 5, 5, 0, 0, 20, {"defense": 2, "dodge_self": .25, "dodge_reduction": -.05, "crit_self": .25, "crit_reduction": -.05}, {"health": 15, "strength": 2, "strength_percent": .15, "agility": 1}, (("opal", 20), ("emerald", 10), ("sulfur", 10))),
        ("Кольцо Древесных Богов", "wood-gods-ring", 80, 10, 25, 6, 5, 5, 0, 20, 0, {"defense": 2, "dodge_self": .20, "dodge_reduction": -.10, "crit_self": .20, "crit_reduction": -.10}, {"health": 15, "strength": 2, "strength_percent": .15, "luck": 1}, (("amethyst", 22), ("ruby", 10), ("sulfur", 10))),
        ("Кольцо Каменного Духа", "stone-spirit-ring", 100, 20, 30, 6, 5, 5, 15, 15, 15, {"defense": 2, "dodge_self": .15, "dodge_reduction": -.15, "crit_self": .15, "crit_reduction": -.15}, {"health": 20, "strength": 1, "strength_percent": .20, "agility": 1, "luck": 1}, (("opal", 25), ("sapphire", 15), ("zinc", 8))),
        ("Кольцо Быстрой Смерти", "fast-death-ring", 120, 15, 25, 6, 5, 5, 15, 13, 17, {"defense": 2, "dodge_reduction": -.30, "crit_self": .30}, {"health": 15, "strength": 1, "strength_percent": .15, "luck": 2}, (("topaz", 25), ("emerald", 15), ("lead", 15))),
        ("Кольцо Воздушной Энергии", "air-energy-ring", 120, 15, 25, 6, 5, 5, 20, 15, 10, {"defense": 2, "dodge_self": .30, "dodge_reduction": -.05, "crit_reduction": -.25}, {"health": 15, "strength": 1, "strength_percent": .15, "agility": 2}, (("amethyst", 25), ("ruby", 15), ("silicon", 20))),

        # Уровень 7
        ("Кольцо Стихии", "elemental-ring", 150, 35, 35, 8, 6, 7, 26, 26, 26, {"defense": 3, "dodge_reduction": -.35, "crit_reduction": -.35}, {"health": 20, "strength_percent": .20, "agility": 2, "luck": 2}, (("opal", 35), ("sapphire", 20), ("tin", 7))),
        ("Кольцо Неприступности", "impregnability-ring", 130, 30, 35, 8, 6, 7, 31, 31, 0, {"defense": 2, "dodge_self": .20, "dodge_reduction": -.20, "crit_self": .20, "crit_reduction": -.20}, {"health": 15, "strength": 1, "strength_percent": .15, "agility": 1, "luck": 2}, (("topaz", 35), ("amethyst", 30), ("opal", 25))),
        ("Кольцо Забвения", "oblivion-ring", 130, 30, 35, 8, 6, 7, 31, 0, 31, {"defense": 2, "dodge_self": .10, "dodge_reduction": -.20, "crit_self": .35, "crit_reduction": -.25}, {"health": 15, "strength": 1, "strength_percent": .05, "agility": 2, "luck": 1}, (("topaz", 35), ("sapphire", 18), ("ruby", 15))),
        ("Кольцо Верности", "fidelity-ring", 130, 35, 35, 8, 6, 7, 0, 31, 31, {"defense": 2, "dodge_self": .30, "dodge_reduction": -.10, "crit_self": .30, "crit_reduction": -.10}, {"health": 15, "strength": 2, "strength_percent": .15, "agility": 1, "luck": 1}, (("topaz", 35), ("opal", 25), ("emerald", 15))),
        ("Кольцо Коварства", "treachery-ring", 170, 30, 35, 8, 6, 7, 36, 26, 36, {"defense": 2, "dodge_reduction": -.35, "crit_self": .35, "crit_reduction": -.10}, {"health": 15, "strength": 1, "strength_percent": .15, "agility": 1, "luck": 2}, (("amethyst", 40), ("emerald", 20), ("ruby", 20))),
        ("Кольцо Бесконечности", "infinity-ring", 170, 35, 35, 8, 6, 7, 30, 40, 26, {"defense": 2, "dodge_self": .40, "dodge_reduction": -.05, "crit_reduction": -.35}, {"health": 10, "strength": 1, "strength_percent": .15, "agility": 2, "luck": 1}, (("amethyst", 35), ("sapphire", 25), ("diamond", 10))),

        # Уровень 9
        ("Кольцо Миротворца", "peacemaker-ring", 270, 35, 40, 10, 7, 9, 55, 35, 35, {"defense": 2, "dodge_self": .25, "dodge_reduction": -.25, "crit_self": .25, "crit_reduction": -.25}, {"health": 20, "strength": 1, "strength_percent": .20, "agility": 2, "luck": 2}, (("topaz", 55), ("amethyst", 50), ("emerald", 25), ("sulfur", 20))),
        ("Кольцо Могущества", "might-ring", 310, 40, 40, 10, 7, 9, 72, 0, 0, {"defense": 2, "dodge_self": .05, "dodge_reduction": -.40, "crit_self": .05, "crit_reduction": -.45}, {"health": 25, "strength": 1, "strength_percent": .25, "agility": 2, "luck": 2}, (("amethyst", 55), ("opal", 45), ("diamond", 15), ("copper", 20))),
        ("Кольцо Непокорного Ветра", "unyielding-wind-ring", 330, 40, 40, 10, 7, 9, 52, 55, 0, {"defense": 2, "dodge_self": .45, "dodge_reduction": -.25, "crit_reduction": -.35}, {"health": 15, "strength": 2, "strength_percent": .20, "agility": 2, "luck": 1}, (("topaz", 55), ("sapphire", 45), ("ruby", 35), ("mica", 20))),
        ("Кольцо Поглощения Тьмы", "darkness-absorption-ring", 320, 45, 45, 10, 7, 9, 60, 32, 32, {"defense": 1, "dodge_reduction": -.30, "crit_reduction": -.30}, {"health": 70, "strength": 3, "strength_percent": .40, "agility": 1, "luck": 2}, (("amethyst", 55), ("sapphire", 45), ("ruby", 30), ("zinc", 15))),
        ("Кольцо Уходящего Света", "fading-light-ring", 350, 40, 40, 10, 7, 9, 52, 37, 37, {"defense": 2, "dodge_self": .45, "dodge_reduction": -.15, "crit_self": .45, "crit_reduction": -.15}, {"health": 10, "agility": 2, "luck": 2}, (("topaz", 55), ("opal", 55), ("diamond", 18), ("lead", 20))),
        ("Кольцо Уверенности", "confidence-ring", 300, 40, 40, 10, 7, 9, 52, 0, 55, {"defense": 2, "dodge_reduction": -.35, "crit_self": .45, "crit_reduction": -.15}, {"health": 15, "strength": 2, "strength_percent": .20, "agility": 1, "luck": 2}, (("opal", 55), ("sapphire", 35), ("emerald", 25), ("silicon", 20))),

        # Уровень 11
        ("Кольцо Подавления", "suppression-ring", 510, 40, 45, 10, 8, 11, 60, 0, 67, {"defense": 3, "dodge_reduction": -.40, "crit_self": .55, "crit_reduction": -.25}, {"health": 10, "strength": 2, "strength_percent": .20, "agility": 2, "luck": 3}, (("topaz", 75), ("opal", 65), ("emerald", 35), ("diamond", 15), ("silicon", 25), ("lead", 15))),
        ("Кольцо Скорпиона", "scorpion-ring", 570, 55, 50, 10, 8, 11, 65, 35, 35, {"defense": 2, "dodge_reduction": -.40, "crit_reduction": -.40}, {"health": 90, "strength": 3, "strength_percent": .45, "agility": 2, "luck": 2}, (("amethyst", 75), ("opal", 70), ("sapphire", 45), ("emerald", 35), ("zinc", 20), ("tin", 10))),
        ("Кольцо Иерарха", "hierarch-ring", 520, 50, 40, 10, 8, 11, 82, 0, 0, {"defense": 3, "dodge_self": .10, "dodge_reduction": -.45, "crit_self": .10, "crit_reduction": -.50}, {"health": 35, "strength": 2, "strength_percent": .35, "agility": 2, "luck": 2}, (("amethyst", 75), ("opal", 65), ("sapphire", 45), ("ruby", 35), ("copper", 25), ("mica", 15))),
        ("Кольцо Отца Гор", "father-of-mountains-ring", 550, 45, 45, 10, 8, 11, 60, 67, 0, {"defense": 3, "dodge_self": .50, "dodge_reduction": -.30, "crit_reduction": -.45}, {"health": 10, "strength": 2, "strength_percent": .20, "agility": 3, "luck": 2}, (("topaz", 75), ("amethyst", 70), ("sapphire", 45), ("diamond", 20), ("sulfur", 30), ("mica", 20))),
        ("Кольцо Симбиоза", "symbiosis-ring", 480, 40, 40, 10, 8, 11, 62, 38, 38, {"defense": 3, "dodge_self": .30, "dodge_reduction": -.30, "crit_self": .30, "crit_reduction": -.30}, {"health": 25, "strength": 1, "strength_percent": .20, "agility": 3, "luck": 3}, (("topaz", 75), ("opal", 60), ("sapphire", 40), ("ruby", 35), ("sulfur", 25), ("zinc", 15))),
        ("Кольцо Вдохновения", "inspiration-ring", 540, 50, 45, 10, 8, 11, 55, 42, 42, {"defense": 3, "dodge_self": .50, "dodge_reduction": -.20, "crit_self": .50, "crit_reduction": -.15}, {"health": 10, "strength": 1, "strength_percent": .05, "agility": 3, "luck": 3}, (("topaz", 75), ("amethyst", 65), ("emerald", 40), ("ruby", 40), ("silicon", 30), ("lead", 20))),
    )
    return tuple(
        ProductionItem(name, f"i.ring.16.{level}.{slug}", ItemType.RING, "1.16.jewelers", price, weight, max_wear, stages, experience, level, requirements(level, strength, agility, luck, max_wear=max_wear, **combat), abilities, components=components)
        for name, slug, price, weight, max_wear, stages, experience, level, strength, agility, luck, combat, abilities, components in rows
    )


# =============================================================================
# ИТОГОВЫЙ КОРТЕЖ ВСЕХ ПРЕДМЕТОВ
# =============================================================================

PRODUCTION_ITEMS = (
    FORGE_SHIELDS
    + _weapons()
    + _axes()
    + _hammers()
    + _cloaks()
    + _bronze_armor()
    + _armor_level_six()
    + _armor_level_eight()
    + _armor_level_ten()
    + _armor_level_twelve()
    + _amulets()
    + _pendants()
    + _rings()
)