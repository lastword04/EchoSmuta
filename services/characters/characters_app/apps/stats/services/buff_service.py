import uuid
from datetime import datetime, timedelta
from typing import Protocol
from typing_extensions import Self

from ..models import CharacterBuff
from ..schemas import ApplyBuffSchema, CharacterBuffReadSchema
from .calculator.aggregator import StatsAggregator



class BuffServiceProtocol(Protocol):
    async def apply_buff(self: Self, data: ApplyBuffSchema) -> CharacterBuffReadSchema | None: ...
    async def remove_buff(self: Self, character_id: uuid.UUID, buff_type: str) -> None: ...
    async def get_character_buffs(self: Self, character_id: uuid.UUID) -> list[CharacterBuffReadSchema]: ...
    async def tick_buffs(self: Self, character_id: uuid.UUID) -> None: ...    


class BuffService(BuffServiceProtocol):
    def __init__(self, repository, character_repository, publisher, collector, modifiers_collector):
        self.repository = repository
        self.character_repository = character_repository
        self.publisher = publisher
        self.collector = collector
        self.modifiers_collector = modifiers_collector

    async def apply_buff(self, data: ApplyBuffSchema) -> CharacterBuffReadSchema | None:
        """Применить бафф к персонажу"""
        
        # Мгновенные эффекты (duration=0)
        if data.duration_seconds == 0:
            await self._apply_instant_effect(data.character_id, data.buff_type, data.value)
            return None
        
        # 1. Пытаемся найти активный buff (может упасть если дубликаты)
        existing_buff = None
        try:
            existing_buff = await self.repository.get_by_character_and_type(
                data.character_id,
                data.buff_type
            )
        except Exception:
            # MultipleResultsFound — дубликаты, игнорируем
            existing_buff = None
        
        # 2. Если нашли активный — проверяем валидацию
        if existing_buff and existing_buff.is_active:
            if existing_buff.expires_at and existing_buff.expires_at > datetime.utcnow():
                from ....core.utils.exceptions import ValidationError
                raise ValidationError(
                    field="buff_type",
                    message=f"У вас уже есть активный эффект типа {data.buff_type}. Дождитесь его истечения."
                )
        
        # 3. Если активного не нашли — деактивируем все дубликаты перед созданием нового
        if not existing_buff:
            await self.repository.deactivate_duplicates(
                character_id=data.character_id,
                buff_type=data.buff_type,
                exclude_id=None
            )

        expires_at = datetime.utcnow() + timedelta(seconds=data.duration_seconds)
        
        if existing_buff:
            # Обновить существующий (был неактивен или истёк)
            existing_buff.value = data.value
            existing_buff.expires_at = expires_at
            existing_buff.source_name = data.source_name
            existing_buff.is_active = True
            updated = await self.repository.update_buff(existing_buff)
            result = CharacterBuffReadSchema.model_validate(updated, from_attributes=True)
        else:
            # Создать новый
            buff = CharacterBuff(
                character_id=data.character_id,
                buff_type=data.buff_type,
                value=data.value,
                duration_seconds=data.duration_seconds,
                expires_at=expires_at,
                source=data.source,
                source_name=data.source_name,
                is_active=True
            )
            created = await self.repository.create_buff(buff)
            result = CharacterBuffReadSchema.model_validate(created, from_attributes=True)
        
        await self.publisher.publish(data.character_id)
        return result

    async def _apply_instant_effect(self, character_id: uuid.UUID, buff_type: str, value) -> None:
        stats = await self.character_repository.get_health_mana(character_id)
        
        # Получить персонажа и рассчитать эффективные максимумы
        character = await self.character_repository.get(character_id)
        modifiers = await self.modifiers_collector.get_all_modifiers(character)
        effective = StatsAggregator.calculate_effective_stats(character, modifiers)
        
        if buff_type == "hp_restore":
            new_health = min(stats["health"] + value, effective["effective_max_health"])
            await self.character_repository.update_health(character_id, new_health)
            
        elif buff_type == "mana_restore":
            new_mana = min(stats["mana"] + value, effective["effective_max_mana"])
            await self.character_repository.update_mana(character_id, new_mana)
            
        elif buff_type == "stamina_restore":
            new_tiredness = max(stats["tiredness"] - value, 0)
            await self.character_repository.update_tiredness(character_id, new_tiredness)

        elif buff_type == "stamina_restore_percent":
            new_tiredness = max(stats["tiredness"] - value * effective["effective_max_tiredness"], 0)
            await self.character_repository.update_tiredness(character_id, new_tiredness)

        await self.publisher.publish_regeneration(character_id)

    

    async def remove_buff(self, character_id: uuid.UUID, buff_type: str) -> None:
        await self.repository.delete_by_character_and_type(character_id, buff_type)
        await self.publisher.publish(character_id)

    async def get_character_buffs(self, character_id):
        buffs = await self.repository.get_active_by_character(character_id)
        alive = await self.collector.get_active_buffs(character_id)

        # Если что-то отсеялось — значит истекло, но tick ещё не отработал.
        if len(alive) != len(buffs):
            await self.publisher.publish(character_id)

        return [CharacterBuffReadSchema.model_validate(b, from_attributes=True) for b in alive]

    async def tick_buffs(self, character_id: uuid.UUID) -> None:
        """Обработка тика баффов (регенерация, истечение)"""
        buffs = await self.repository.get_active_by_character(character_id)
        now = datetime.utcnow()
        expired_any = False
        
        for buff in buffs:
            # Проверить, истёк ли бафф
            if buff.expires_at and buff.expires_at <= now:
                buff.is_active = False
                await self.repository.update_buff(buff)
                expired_any = True
                continue
            
            # Применить периодический эффект
            await self._apply_periodic_effect(character_id, buff)
        
        # Если буст истёк — публикуем обновлённые статы (буст перестал действовать)
        if expired_any:
            await self.publisher.publish(character_id)

    async def _apply_periodic_effect(self, character_id: uuid.UUID, buff: CharacterBuff) -> None:
        if buff.buff_type == "hp_regen":
            stats = await self.character_repository.get_health_mana(character_id)
            new_health = min(stats["health"] + buff.value, stats["max_health"])
            await self.character_repository.update_health(character_id, new_health)
        elif buff.buff_type == "mana_regen":
            stats = await self.character_repository.get_health_mana(character_id)
            new_mana = min(stats["mana"] + buff.value, stats["max_mana"])
            await self.character_repository.update_mana(character_id, new_mana)
   