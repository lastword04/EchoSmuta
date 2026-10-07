from .collector.modifiers import ModifiersCollector
from .calculator.aggregator import StatsAggregator


class EffectiveStatsService:
    """Считает эффективные статы для любого объекта персонажа (ORM или схема)."""

    def __init__(self, modifiers_collector: ModifiersCollector):
        self.modifiers_collector = modifiers_collector

    async def calculate(self, character) -> dict:
        modifiers = await self.modifiers_collector.get_all_modifiers(character)
        return StatsAggregator.calculate_effective_stats(character, modifiers)