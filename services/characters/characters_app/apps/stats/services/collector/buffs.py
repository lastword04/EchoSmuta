import uuid
from datetime import datetime
from ...models import StatModifier, MOD_FLAT, CONTEXT_ALWAYS


# Какие buff_type влияют на статы и на какие именно.
# hp_regen / mana_regen сюда НЕ входят: это периодические эффекты
# (тикают и лечат), а не модификаторы статов.
BUFF_TYPE_TO_STAT = {
    "strength_boost": "strength",
    "agility_boost": "agility",
    "luck_boost": "lucky",
}


class BuffsCollector:
    """Собирает данные об активных баффах персонажа: бонусы и список для фронта."""

    def __init__(self, buff_repository):
        self.repository = buff_repository

    async def get_active_buffs(self, character_id: uuid.UUID) -> list:
        """Активные баффы: не истёкшие по времени."""
        buffs = await self.repository.get_active_by_character(character_id)
        now = datetime.utcnow()
        return [b for b in buffs if not b.expires_at or b.expires_at > now]
    

    async def get_buffs_for_frontend(self, character_id: uuid.UUID) -> list[dict]:
        """Список активных баффов для WebSocket-сообщения."""
        return [
            {
                "id": str(b.id),
                "buff_type": b.buff_type,
                "value": b.value,
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "duration_seconds": b.duration_seconds,
                "source": b.source,
                "source_name": b.source_name,
                "is_active": b.is_active,
                "stack_count": b.stack_count,
            }
            for b in await self.get_active_buffs(character_id)
        ]

    async def get_modifiers(self, character) -> list[StatModifier]:
        """Строит модификаторы из активных баффов персонажа."""
        modifiers = []
        for buff in await self.get_active_buffs(character.id):
            if not buff.is_active:
                continue
            stat = BUFF_TYPE_TO_STAT.get(buff.buff_type)
            if not stat:
                continue
            modifiers.append(
                StatModifier(
                    source_type="buff",
                    source_id=str(buff.id),
                    stat=stat,
                    value=buff.value or 0,
                    modifier_type=MOD_FLAT,
                    context=CONTEXT_ALWAYS,
                    applied_at=buff.created_at,
                )
            )
        return modifiers