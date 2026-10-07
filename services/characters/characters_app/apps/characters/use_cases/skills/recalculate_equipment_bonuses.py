import uuid
import logging
from typing_extensions import Self

from .....core.use_cases import UseCaseProtocol
from ...repositories.character.characters import CharacterRepositoryProtocol
from ....stats.services.publisher.stats_publisher import StatsPublisher
from ....stats.services.calculator.scaler import StatScaler
from shared.schemas.base import StatusOkSchema

logger = logging.getLogger(__name__)


class RecalculateEquipmentBonusesUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, character_id: uuid.UUID, new_bonuses: dict) -> StatusOkSchema: ...


class RecalculateEquipmentBonusesUseCase(RecalculateEquipmentBonusesUseCaseProtocol):
    def __init__(self, character_repository: CharacterRepositoryProtocol, publisher: StatsPublisher):
        self.character_repo = character_repository
        self.publisher = publisher

    async def __call__(self: Self, character_id: uuid.UUID, new_bonuses: dict) -> StatusOkSchema:
        """
        Пересчитывает бонусы экипировки персонажа.        
        """
        character_data = await self.character_repo.get_health_mana(character_id)
        character_full = await self.character_repo.get(character_id)

        current_health = character_data["health"]
        current_mana = character_data["mana"]
        current_tiredness = character_data["tiredness"]

        base_max_health = character_data["max_health"]
        base_max_mana = character_data["max_mana"]
        base_max_tiredness = character_data["max_tiredness"]

        old_equipment_bonuses = character_full.equipment_bonuses or {}

        # Применяем только flat бонусы к effective max статам
        old_effective_max_health = base_max_health + old_equipment_bonuses.get('max_health_bonus', 0)
        old_effective_max_mana = base_max_mana + old_equipment_bonuses.get('max_mana_bonus', 0)
        old_effective_max_tiredness = base_max_tiredness + old_equipment_bonuses.get('max_tiredness_bonus', 0)

        new_effective_max_health = base_max_health + new_bonuses.get('max_health_bonus', 0)
        new_effective_max_mana = base_max_mana + new_bonuses.get('max_mana_bonus', 0)
        new_effective_max_tiredness = base_max_tiredness + new_bonuses.get('max_tiredness_bonus', 0)

        is_health_increasing = new_effective_max_health > old_effective_max_health
        is_mana_increasing = new_effective_max_mana > old_effective_max_mana
        is_tiredness_increasing = new_effective_max_tiredness > old_effective_max_tiredness
       
        new_health = StatScaler.scale(current_health, old_effective_max_health, new_effective_max_health, is_health_increasing)
        new_mana = StatScaler.scale(current_mana, old_effective_max_mana, new_effective_max_mana, is_mana_increasing)
        new_tiredness = StatScaler.scale(current_tiredness, old_effective_max_tiredness, new_effective_max_tiredness, is_tiredness_increasing)

        await self.character_repo.update_equipment_bonuses(character_id, new_bonuses)

        if new_health != current_health:
            await self.character_repo.update_health(character_id, new_health)
        if new_mana != current_mana:
            await self.character_repo.update_mana(character_id, new_mana)
        if new_tiredness != current_tiredness:
            await self.character_repo.update_tiredness(character_id, new_tiredness)       

        await self.publisher.publish(character_id)

        logger.info(f"Equipment bonuses recalculated for character {character_id}")
        return StatusOkSchema(status="ok")

  