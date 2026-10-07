import json
import uuid

import redis.asyncio as redis

from ....characters.repositories.character.characters import CharacterRepositoryProtocol
from ..collector.buffs import BuffsCollector
from ..collector.modifiers import ModifiersCollector
from ..calculator.aggregator import StatsAggregator


class StatsPublisher:
    """Единственная точка публикации статов персонажа в WebSocket."""

    def __init__(
        self,
        redis_client: redis.Redis,
        character_repository: CharacterRepositoryProtocol,
        modifiers_collector: ModifiersCollector,
        buffs_collector: BuffsCollector,
    ):
        self.redis = redis_client
        self.character_repository = character_repository
        self.modifiers_collector = modifiers_collector
        self.buffs_collector = buffs_collector

    async def publish(self, character_id: uuid.UUID) -> None:
        character = await self.character_repository.get(character_id)
        if not character:
            return

        equipment = character.equipment_bonuses or {}
        modifiers = await self.modifiers_collector.get_all_modifiers(character)
        effective = StatsAggregator.calculate_effective_stats(character, modifiers)
        buffs = await self.buffs_collector.get_buffs_for_frontend(character.id)       

        payload = {
            "health": round(float(character.health)),
            "effective_max_health": effective["effective_max_health"],
            "mana": round(float(character.mana)),
            "effective_max_mana": effective["effective_max_mana"],
            "tiredness": round(float(character.tiredness), 2),
            "effective_max_tiredness": effective["effective_max_tiredness"],
            "effective_power": effective["effective_power"],
            "effective_agility": effective["effective_agility"],
            "effective_lucky": effective["effective_lucky"],
            "equipment_bonuses": equipment,           
            "buffs": buffs,
            "event": "stats_updated",
        }

        channel = f"character:{character_id}:stats"
        await self.redis.publish(channel, json.dumps(payload))


    async def publish_regeneration(self, character_id: uuid.UUID) -> None:
        stats = await self.character_repository.get_health_mana(character_id)
        payload = {
            "health": round(float(stats["health"])),
            "mana": round(float(stats["mana"])),
            "tiredness": round(float(stats["tiredness"]), 2),
            "event": "stats_updated",
        }
        channel = f"character:{character_id}:stats"
        await self.redis.publish(channel, json.dumps(payload))