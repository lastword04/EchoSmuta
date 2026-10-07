import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from ....core.utils.exceptions import ValidationError
from ...characters.models import Character
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ...characters.events.change_location import ChangeLocationEventsProtocol
from ...stats.services.publisher.stats_publisher import StatsPublisher
from ..repositories.inn_repository import RestRepositoryProtocol
from ..models import RestRental

from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope
from ..events.rest_events import RestEventsProtocol
from .rest_templates import RestTemplateServiceProtocol

logger = logging.getLogger(__name__)

def _days_text(days: int) -> str:
    if days % 10 == 1 and days % 100 != 11:
        return f"{days} день"
    if days % 10 in (2, 3, 4) and days % 100 not in (12, 13, 14):
        return f"{days} дня"
    return f"{days} дней"


class RestServiceProtocol:
    async def rent_room(self, character: Character, days: int) -> RestRental: ...
    async def exit_room(self, character: Character) -> None: ...
    async def enter_room(self, character: Character) -> None: ...
    async def get_status(self, character: Character) -> dict: ...
    async def sync_expiry(self, character: Character) -> dict: ...
    async def expire_rentals(self) -> list[uuid.UUID]: ...
    async def sync_on_location_change(self, character: Character, new_location_slug: str) -> None: ...


class RestService(RestServiceProtocol):
    def __init__(
        self,
        rest_repository: RestRepositoryProtocol,
        character_repository: CharacterRepositoryProtocol,
        publisher: StatsPublisher,
        settings,
        events: RestEventsProtocol,
        template_service: RestTemplateServiceProtocol,
        change_location_events: ChangeLocationEventsProtocol,
    ):
        self.rest_repo = rest_repository
        self.char_repo = character_repository
        self.publisher = publisher
        self.settings = settings
        self.events = events
        self.template_service = template_service
        self.change_location_events = change_location_events

    def calculate_price(self, level: int, days: int) -> Decimal:
        base_rate = Decimal("0.35") + Decimal("0.40") * Decimal(level)
        discount = Decimal(str(self.settings.rest_discount_coefficient)) * days * (days - 1) / 2
        multiplier = Decimal(days) - discount
        return base_rate * multiplier

    async def rent_room(self, character: Character, days: int) -> RestRental:
        if character.location_slug != self.settings.rest_location_slug:
            raise ValidationError(field="location", message="Персонаж должен находиться в гостинице")

        stale = await self.rest_repo.get_expired_rental_for_character(
            character.id, datetime.now(timezone.utc)
        )
        if stale:
            await self._cleanup_expired_rental(stale)

        if not stale and character.rest_state == "inside":
            raise ValidationError(field="rest_state", message="Персонаж уже в номере")

        if days < 1 or days > 5:
            raise ValidationError(field="days", message="Допустимо от 1 до 5 дней")

        existing = await self.rest_repo.get_active_rental(character.id)
        if existing:
            raise ValidationError(field="rental", message="Вы уже арендовали номер")

        price = self.calculate_price(character.level, days)
        if character.ducats < price:
            raise ValidationError(field="ducats", message="Недостаточно дукатов")

        count = await self.rest_repo.count_active_rentals()
        if count >= self.settings.rest_max_rooms:
            raise ValidationError(field="rooms", message="Все номера заняты")

        success = await self.char_repo.subtract_ducats(character.id, price)
        if not success:
            raise ValidationError(field="ducats", message="Недостаточно дукатов")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=days)
        room_number = await self.rest_repo.get_first_free_room_number(self.settings.rest_max_rooms)

        rental = await self.rest_repo.create_rental(
            character_id=character.id,
            room_number=room_number,
            days=days,
            rented_at=now,
            expires_at=expires_at
        )

        await self.char_repo.update_rest_state(character.id, "inside")
        await self.char_repo.update_current_room_id(character.id, "inn:inside")
        await self.publisher.publish_regeneration(character.id)

        await self.change_location_events.publish_room_change(
            character_id=character.id,
            name=character.name,
            level=character.level,
            race=character.race.value if character.race else None,
            old_room_slug=self.settings.rest_location_slug,
            new_room_slug="inn:inside",
        )

        try:
            message = self.template_service.get_rent_message(
                inn_name=self.settings.rest_inn_name,
                days_text=_days_text(days),
            )
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="rest_rent",
                    character_id=character.id,
                    location_slug=character.location_slug or self.settings.rest_location_slug,
                    content=message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character.id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish rest_rent event: {e}")

        await self.events.publish_state_event(self.settings.rest_location_slug)
        return rental

    async def exit_room(self, character: Character) -> None:
        if character.rest_state != "inside":
            raise ValidationError(field="rest_state", message="Персонаж не в номере")

        await self.char_repo.update_rest_state(character.id, "entrance")
        await self.char_repo.update_current_room_id(character.id, None)
        await self.publisher.publish_regeneration(character.id)

        await self.change_location_events.publish_room_change(
            character_id=character.id,
            name=character.name,
            level=character.level,
            race=character.race.value if character.race else None,
            old_room_slug="inn:inside",
            new_room_slug=self.settings.rest_location_slug,
        )

        await self.events.publish_state_event(self.settings.rest_location_slug)

    async def enter_room(self, character: Character) -> None:
        rental = await self.rest_repo.get_active_rental(character.id)
        if not rental:
            raise ValidationError(field="rental", message="Нет активной аренды")

        if character.rest_state == "inside":
            raise ValidationError(field="rest_state", message="Персонаж уже в номере")

        if character.rest_state != "entrance":
            raise ValidationError(field="rest_state", message="Персонаж не на входе")

        await self.char_repo.update_rest_state(character.id, "inside")
        await self.char_repo.update_current_room_id(character.id, "inn:inside")
        await self.publisher.publish_regeneration(character.id)

        await self.change_location_events.publish_room_change(
            character_id=character.id,
            name=character.name,
            level=character.level,
            race=character.race.value if character.race else None,
            old_room_slug=self.settings.rest_location_slug,
            new_room_slug="inn:inside",
        )

        await self.events.publish_state_event(self.settings.rest_location_slug)

    async def sync_on_location_change(self, character: Character, new_location_slug: str) -> None:
        """Реакция на смену локации персонажа.

        Вошёл в локацию гостиницы и есть активная аренда — автовход в номер.
        Ушёл из локации гостиницы и был inside — сбрасываем в entrance/None.
        """
        if new_location_slug == self.settings.rest_location_slug:
            # Вошёл в локацию гостиницы — автовход, если есть аренда.
            if character.rest_state == "inside":
                return
            rental = await self.rest_repo.get_active_rental(character.id)
            if rental is None:
                return
            await self.char_repo.update_rest_state(character.id, "inside")
            await self.char_repo.update_current_room_id(character.id, "inn:inside")
            await self.publisher.publish_regeneration(character.id)

            await self.change_location_events.publish_room_change(
                character_id=character.id,
                name=character.name,
                level=character.level,
                race=character.race.value if character.race else None,
                old_room_slug=new_location_slug,
                new_room_slug="inn:inside",
            )
            return

        # Ушёл из локации гостиницы.
        if character.rest_state != "inside":
            return
        rental = await self.rest_repo.get_active_rental(character.id)
        new_state = "entrance" if rental is not None else None
        await self.char_repo.update_rest_state(character.id, new_state)
        await self.char_repo.update_current_room_id(character.id, None)
        await self.publisher.publish_regeneration(character.id)
        # Публикацию здесь НЕ делаем: событие о смене локации уже опубликовал
        # ChangeCharacterLocationUseCase через update_character_location,
        # и оно корректно отписало чат от 'inn:inside' на новую локацию.

    async def get_status(self, character: Character) -> dict:
        rental = await self.rest_repo.get_active_rental(character.id)

        # Аренда истекла — персонаж уже не внутри, даже если Celery ещё не сбросил поле
        effective_state = character.rest_state
        if effective_state == "inside" and rental is None:
            effective_state = "entrance"

        prices = {
            str(d): str(self.calculate_price(character.level, d))
            for d in range(1, 6)
        }

        return {
            "location_slug": character.location_slug,
            "rest_state": effective_state,
            "has_active_rental": rental is not None,
            "room_number": rental.room_number if rental else None,
            "expires_at": rental.expires_at.isoformat() if rental else None,
            "days": rental.days if rental else None,
            "prices": prices,
            "max_rooms": self.settings.rest_max_rooms,
            "available_rooms": self.settings.rest_max_rooms - await self.rest_repo.count_active_rentals()
        }   

    async def expire_rentals(self) -> list[uuid.UUID]:
        now = datetime.now(timezone.utc)
        expired = await self.rest_repo.get_expired_rentals(now)
        character_ids = []

        for rental in expired:
            if await self._cleanup_expired_rental(rental):
                character_ids.append(rental.character_id)

        return character_ids

    async def _cleanup_expired_rental(self, rental: RestRental) -> bool:
        """Идемпотентный cleanup: кто первый удалил строку, тот и убирает последствия."""
        deleted = await self.rest_repo.expire_rental(rental.id)
        if not deleted:
            return False

        await self.rest_repo.create_history(
            character_id=rental.character_id,
            days=rental.days,
            rented_at=rental.rented_at,
            expired_at=rental.expires_at,
        )
        await self.char_repo.update_rest_state(rental.character_id, "entrance")
        await self.char_repo.update_current_room_id(rental.character_id, None)
        await self.publisher.publish_regeneration(rental.character_id)

        # Публикуем переход только если игрок онлайн — иначе некому.
        expired_character = await self.char_repo.get(rental.character_id)
        if expired_character is not None and expired_character.is_online:
            await self.change_location_events.publish_room_change(
                character_id=expired_character.id,
                name=expired_character.name,
                level=expired_character.level,
                race=expired_character.race.value if expired_character.race else None,
                old_room_slug="inn:inside",
                new_room_slug=self.settings.rest_location_slug,
            )

        try:
            message = self.template_service.get_expired_message(
                inn_name=self.settings.rest_inn_name,
            )
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="rest_rent_expired",
                    character_id=rental.character_id,
                    location_slug=self.settings.rest_location_slug,
                    content=message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[rental.character_id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish rest_rent_expired event: {e}")

        await self.events.publish_state_event(self.settings.rest_location_slug)
        return True

    async def sync_expiry(self, character: Character) -> dict:
        now = datetime.now(timezone.utc)
        rental = await self.rest_repo.get_expired_rental_for_character(character.id, now)
        if rental is None:
            return {"expired": False}
        cleaned = await self._cleanup_expired_rental(rental)
        return {"expired": cleaned}