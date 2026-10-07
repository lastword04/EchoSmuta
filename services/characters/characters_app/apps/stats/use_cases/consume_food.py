import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol

from shared.schemas.base import StatusOkSchema
from ....core.utils.exceptions import ValidationError
from ..schemas import ConsumeFoodSchema
from ..services.buff_service import BuffServiceProtocol


ALLOWED_FOOD_EFFECTS = {"hp_restore", "stamina_restore_percent"}


class ConsumeFoodUseCaseProtocol(Protocol):
    async def __call__(self, data: ConsumeFoodSchema) -> StatusOkSchema: ...


class ConsumeFoodUseCase(ConsumeFoodUseCaseProtocol):
    def __init__(self, buff_service: BuffServiceProtocol, character_repository):
        self.buff_service = buff_service
        self.character_repository = character_repository

    async def __call__(self, data: ConsumeFoodSchema) -> StatusOkSchema:
        # 1. Получить персонажа
        character = await self.character_repository.get(data.character_id)
        if character is None:
            raise ValidationError(
                field="character_id",
                message="Персонаж не найден.",
            )

        # 2. Проверить кулдаун еды
        now = datetime.now(timezone.utc)
        if character.food_cooldown_until is not None:
            cooldown_until = character.food_cooldown_until
            # Убедиться, что сравниваем в одной таймзоне
            if cooldown_until.tzinfo is None:
                cooldown_until = cooldown_until.replace(tzinfo=timezone.utc)
            if now < cooldown_until:
                remaining_seconds = int((cooldown_until - now).total_seconds())
                remaining_minutes = remaining_seconds // 60
                if remaining_minutes > 0:
                    message = f"Вы недавно ели. Подождите ещё {remaining_minutes} мин."
                else:
                    message = f"Вы недавно ели. Подождите ещё {remaining_seconds} сек."
                raise ValidationError(
                    field="food_cooldown",
                    message=message,
                )

        # 3. Проверить локацию, если требуется
        if data.required_location_slug:
            if character.location_slug != data.required_location_slug:
                raise ValidationError(
                    field="location_slug",
                    message="Вы находитесь не в той локации.",
                )

        # 4. Проверить типы эффектов ДО применения
        for effect in data.effects:
            if effect.effect_type not in ALLOWED_FOOD_EFFECTS:
                raise ValidationError(
                    field="effects",
                    message=f"Неподдерживаемый тип эффекта еды: {effect.effect_type}.",
                )

        # 5. Применить каждый эффект
        for effect in data.effects:
            await self.buff_service._apply_instant_effect(
                character_id=data.character_id,
                buff_type=effect.effect_type,
                value=effect.value,
            )

        # 6. Установить новый кулдаун
        new_cooldown_until = now + timedelta(seconds=data.cooldown_seconds)
        await self.character_repository.update_food_cooldown(
            data.character_id,
            new_cooldown_until,
        )

        return StatusOkSchema()