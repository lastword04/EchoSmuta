from ...models import StatModifier


class ModifiersCollector:
    """
    Главный collector: опрашивает все collector'ы источников
    и складывает их модификаторы в один список.
    Сам в базу не ходит.
    """

    def __init__(self, collectors: list):
        self.collectors = collectors

    async def get_all_modifiers(self, character) -> list[StatModifier]:
        modifiers = []
        for collector in self.collectors:
            modifiers.extend(await collector.get_modifiers(character))
        return modifiers