import logging
import uuid
from datetime import datetime, timedelta, timezone

from ....core.utils.exceptions import ValidationError
from ...characters.models import Character
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ...characters.events.change_location import ChangeLocationEventsProtocol
from ...stats.services.publisher.stats_publisher import StatsPublisher
from ..events.house_events import HouseEventsProtocol
from ..events.rest_events import RestEventsProtocol
from ..models import House
from ..repositories.house_repository import HouseRepositoryProtocol
from ..repositories.house_furniture_repository import HouseFurnitureRepositoryProtocol
from ..repositories.house_guest_request_repository import HouseGuestRequestRepositoryProtocol
from ..repositories.house_guest_session_repository import HouseGuestSessionRepositoryProtocol
from .rest_templates import RestTemplateServiceProtocol

from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

logger = logging.getLogger(__name__)

GUEST_REQUEST_TTL_SECONDS = 60


class HouseGuestServiceProtocol:
    async def knock(self, character: Character, house_id: uuid.UUID) -> None: ...
    async def accept_guest_request(self, character: Character, request_id: uuid.UUID) -> dict: ...
    async def reject_guest_request(self, character: Character, request_id: uuid.UUID) -> dict: ...
    async def kick_guest(self, character: Character, guest_character_id: uuid.UUID) -> dict: ...
    async def get_guests(self, character: Character, house_id: uuid.UUID) -> dict: ...
    async def expire_requests(self) -> int: ...
    async def leave_on_location_change(self, character: Character, new_location_slug: str) -> None: ...
    async def leave_on_offline(self, character: Character) -> None: ...


class HouseGuestService(HouseGuestServiceProtocol):
    def __init__(
        self,
        house_repository: HouseRepositoryProtocol,
        character_repository: CharacterRepositoryProtocol,
        guest_request_repository: HouseGuestRequestRepositoryProtocol,
        guest_session_repository: HouseGuestSessionRepositoryProtocol,
        furniture_repository: HouseFurnitureRepositoryProtocol,
        mining_client,
        publisher: StatsPublisher,
        settings,
        events: RestEventsProtocol,
        template_service: RestTemplateServiceProtocol,
        house_events: HouseEventsProtocol,
        change_location_events: ChangeLocationEventsProtocol,
    ):
        self.house_repo = house_repository
        self.char_repo = character_repository
        self.guest_request_repo = guest_request_repository
        self.guest_session_repo = guest_session_repository
        self.furniture_repo = furniture_repository
        self.mining_client = mining_client
        self.publisher = publisher
        self.settings = settings
        self.events = events
        self.template_service = template_service
        self.house_events = house_events
        self.change_location_events = change_location_events

    async def expire_requests(self) -> int:
        return await self.guest_request_repo.expire_old(datetime.now(timezone.utc))

    async def _build_owner_response(self, house: House, owner: Character) -> dict:
        return {
            "house": await self._build_house_view_payload(
                house, is_owner=True, owner_name=owner.name,
            ),
            "requests": await self._requests_payload(house.id),
        }

    async def _build_house_view_payload(
        self, house: House, is_owner: bool, owner_name: str,
    ) -> dict:
        """Payload дома для конкретного наблюдателя (владелец или гость).

        Отличается от _build_owner_response отсутствием списка заявок:
        заявки видит только владелец и только через get_status/get_guests.
        """
        return {
            "id": str(house.id),
            "number": house.number,
            "capacity": house.capacity,
            "current_volume": house.current_volume,
            "bonuses": {
                stat: round((mult - 1.0) * 100)
                for stat, mult in (house.regen_multipliers or {}).items()
            },
            "wallpaper_photo_id": str(house.wallpaper_photo_id) if house.wallpaper_photo_id else None,
            "furniture": await self._furniture_payload(house),
            "is_owner": is_owner,
            "owner_name": owner_name,
            "guests_count": await self.guest_session_repo.count_by_house(house.id),
            "guests": await self._guests_payload(house.id),
        }

    async def _furniture_payload(self, house: House) -> list[dict]:
        owner_list = await self.mining_client.get_character_furniture(house.owner_character_id)
        items_by_id = {f.inventory_item_id: f for f in owner_list}
        records = await self.furniture_repo.list_by_house(house.id)
        result = []
        for record in records:
            item = items_by_id.get(record.inventory_item_id)
            if item is None:
                continue
            result.append({
                "house_id": house.id,
                "inventory_item_id": record.inventory_item_id,
                "slug": item.slug,
                "wear": item.wear,
                "max_wear": item.max_wear,
                "volume": item.volume,
                "weight": item.weight,
                "ability_parameters": item.ability_parameters,
                "name": item.name,
            })
        return result

    async def _guests_payload(self, house_id: uuid.UUID) -> list[dict]:
        sessions = await self.guest_session_repo.list_by_house(house_id)
        result = []
        for s in sessions:
            guest = await self.char_repo.get(s.character_id)
            result.append({
                "character_id": str(s.character_id),
                "name": guest.name if guest is not None else "—",
            })
        return result

    async def _requests_payload(self, house_id: uuid.UUID) -> list[dict]:
        now = datetime.now(timezone.utc)
        pending = await self.guest_request_repo.list_pending_by_house(house_id, now)
        result = []
        for r in pending:
            knocker = await self.char_repo.get(r.character_id)
            result.append({
                "id": str(r.id),
                "character_id": r.character_id,
                "name": knocker.name if knocker is not None else "—",
                "expires_at": r.expires_at,
            })
        return result

    async def knock(self, character: Character, house_number: int) -> None:
        if character.location_slug != self.settings.residential_location_slug:
            raise ValidationError(field="location", message="Персонаж должен находиться в локации Частные дома")
        if character.current_house_id is not None:
            raise ValidationError(field="current_house_id", message="Вы уже находитесь в доме")

        house = await self.house_repo.get_by_number(house_number)
        if house is None:
            raise ValidationError(field="house_number", message="Дом не найден")
        if house.owner_character_id == character.id:
            raise ValidationError(field="house_number", message="Это ваш дом")

        owner = await self.char_repo.get(house.owner_character_id)
        if owner is None or owner.current_house_id != house.id:
            raise ValidationError(field="house_id", message="Владельца нет дома")

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=GUEST_REQUEST_TTL_SECONDS)
        await self.guest_request_repo.upsert_knock(
            house_id=house.id,
            character_id=character.id,
            expires_at=expires_at,
        )

        try:
            message = self.template_service.get_house_knock_message(number=house.number)
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="house_knock_self",
                    character_id=character.id,
                    location_slug=character.location_slug or self.settings.residential_location_slug,
                    content=message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character.id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish house knock event: {e}")

        await self.house_events.publish(
            action="guest_knocked",
            house_id=house.id,
            target_user_ids=[house.owner_character_id],
        )

    async def accept_guest_request(self, character: Character, request_id: uuid.UUID) -> dict:
        request = await self.guest_request_repo.get_by_id(request_id)
        if request is None:
            raise ValidationError(field="request_id", message="Заявка не найдена")

        house = await self.house_repo.get_by_id(request.house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")
        if house.owner_character_id != character.id:
            raise ValidationError(field="request_id", message="Это не ваша заявка")
        if character.current_house_id != house.id:
            raise ValidationError(field="current_house_id", message="Вы должны находиться внутри дома")

        now = datetime.now(timezone.utc)
        if request.expires_at <= now:
            await self.guest_request_repo.delete_by_id(request_id)
            raise ValidationError(field="request_id", message="Заявка истекла")

        guests_count = await self.guest_session_repo.count_by_house(house.id)
        if guests_count >= self.settings.house_max_guests:
            raise ValidationError(field="capacity", message="В доме нет мест для гостей")

        guest = await self.char_repo.get(request.character_id)
        if (
            guest is None
            or guest.location_slug != self.settings.residential_location_slug
            or guest.current_house_id is not None
        ):
            await self.guest_request_repo.delete_by_id(request_id)
            raise ValidationError(field="request_id", message="Гость больше не ждёт у дверей")

        await self.guest_session_repo.create(house_id=house.id, character_id=guest.id)
        await self.guest_request_repo.delete_by_id(request_id)
        await self.char_repo.update_current_house_id(guest.id, house.id)
        await self.char_repo.update_current_room_id(guest.id, f"house:{house.id}")
        await self.publisher.publish_regeneration(guest.id)

        await self.change_location_events.publish_room_change(
            character_id=guest.id,
            name=guest.name,
            level=guest.level,
            race=guest.race.value if guest.race else None,
            old_room_slug=guest.location_slug,
            new_room_slug=f"house:{house.id}",
        )

        try:
            guest_message = self.template_service.get_house_accepted_guest_message(number=house.number)
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="house_accepted_guest",
                    character_id=guest.id,
                    location_slug=self.settings.residential_location_slug,
                    content=guest_message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[guest.id],
                )
            )
            owner_message = self.template_service.get_house_accepted_owner_message(character_name=guest.name)
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="house_accepted_owner",
                    character_id=character.id,
                    location_slug=self.settings.residential_location_slug,
                    content=owner_message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character.id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish house accept events: {e}")

        # Payload дома глазами гостя: is_owner=False, owner_name=имя владельца.
        # Он уедет вместе с WS-событием, чтобы фронт гостя отрисовал дом
        # в том же тике, что и переключение заголовка/чата — без ожидания
        # refetch getHousesStatus и без промежуточного кадра с улицей.
        guest_house_payload = await self._build_house_view_payload(
            house, is_owner=False, owner_name=character.name,
        )
        await self.house_events.publish(
            action="guest_accepted",
            house_id=house.id,
            target_user_ids=[character.id, guest.id],
            affected_character_id=guest.id,
            house_payload=guest_house_payload,
        )

        return await self._build_owner_response(house, character)

    async def reject_guest_request(self, character: Character, request_id: uuid.UUID) -> dict:
        request = await self.guest_request_repo.get_by_id(request_id)
        if request is None:
            raise ValidationError(field="request_id", message="Заявка не найдена")

        house = await self.house_repo.get_by_id(request.house_id)
        if house is None or house.owner_character_id != character.id:
            raise ValidationError(field="request_id", message="Это не ваша заявка")
        if character.current_house_id != house.id:
            raise ValidationError(field="current_house_id", message="Вы должны находиться внутри дома")

        await self.guest_request_repo.delete_by_id(request_id)

        return await self._build_owner_response(house, character)

    async def kick_guest(self, character: Character, guest_character_id: uuid.UUID) -> dict:
        if character.current_house_id is None:
            raise ValidationError(field="current_house_id", message="Вы не в доме")
        house = await self.house_repo.get_by_id(character.current_house_id)
        if house is None or house.owner_character_id != character.id:
            raise ValidationError(field="current_house_id", message="Вы не владелец этого дома")

        session = await self.guest_session_repo.get_by_character(guest_character_id)
        if session is None or session.house_id != house.id:
            raise ValidationError(field="character_id", message="Гость не находится в вашем доме")

        await self.guest_session_repo.delete_by_character(guest_character_id)
        await self.char_repo.update_current_house_id(guest_character_id, None)
        await self.char_repo.update_current_room_id(guest_character_id, None)
        await self.publisher.publish_regeneration(guest_character_id)

        guest = await self.char_repo.get(guest_character_id)

        if guest is not None:
            await self.change_location_events.publish_room_change(
                character_id=guest.id,
                name=guest.name,
                level=guest.level,
                race=guest.race.value if guest.race else None,
                old_room_slug=f"house:{house.id}",
                new_room_slug=guest.location_slug,
            )
        try:
            message = self.template_service.get_house_kicked_owner_message(
                character_name=guest.name if guest is not None else str(guest_character_id),
            )
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="house_kicked_owner",
                    character_id=character.id,
                    location_slug=self.settings.residential_location_slug,
                    content=message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character.id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish house kick event: {e}")

        await self.house_events.publish(
            action="guest_kicked",
            house_id=house.id,
            target_user_ids=[guest_character_id, character.id],
            affected_character_id=guest_character_id,
        )

        return await self._build_owner_response(house, character)

    async def get_guests(self, character: Character, house_id: uuid.UUID) -> dict:
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")

        sessions = await self.guest_session_repo.list_by_house(house_id)
        guests = []
        for s in sessions:
            guest = await self.char_repo.get(s.character_id)
            guests.append({"character_id": s.character_id, "name": guest.name if guest is not None else "—"})

        requests = []
        if house.owner_character_id == character.id and character.current_house_id == house.id:
            now = datetime.now(timezone.utc)
            pending = await self.guest_request_repo.list_pending_by_house(house_id, now)
            for r in pending:
                knocker = await self.char_repo.get(r.character_id)
                requests.append({
                    "id": r.id,
                    "character_id": r.character_id,
                    "name": knocker.name if knocker is not None else "—",
                    "expires_at": r.expires_at,
                })

        return {"guests": guests, "requests": requests}

    async def leave_on_location_change(self, character: Character, new_location_slug: str) -> None:
        """Персонаж ушёл из локации Частные дома в другую — сбрасываем current_house_id для всех."""
        if character.current_house_id is None:
            return
        if new_location_slug == self.settings.residential_location_slug:
            return

        house_id = character.current_house_id
        session = await self.guest_session_repo.get_by_character(character.id)
        was_guest = session is not None and session.house_id == house_id

        # Если был гостем — удаляем гостевую сессию
        if was_guest:
            await self.guest_session_repo.delete_by_character(character.id)

        # Сбрасываем current_house_id для всех (и владельца, и гостей)
        await self.char_repo.update_current_house_id(character.id, None)
        await self.char_repo.update_current_room_id(character.id, None)
        await self.publisher.publish_regeneration(character.id)

        house = await self.house_repo.get_by_id(house_id)
        if house is not None:
            # Публикуем событие только для бывших гостей
            if was_guest:
                await self.house_events.publish(
                    action="guest_left",
                    house_id=house_id,
                    target_user_ids=[house.owner_character_id, character.id],
                    affected_character_id=character.id,
                )

    async def leave_on_offline(self, character: Character) -> None:
        """Гость ушёл в оффлайн — выключаем его из дома. Владелец остаётся в своём доме."""
        if character.current_house_id is None:
            return

        house_id = character.current_house_id
        session = await self.guest_session_repo.get_by_character(character.id)
        was_guest = session is not None and session.house_id == house_id
        if not was_guest:
            return

        await self.guest_session_repo.delete_by_character(character.id)
        await self.char_repo.update_current_house_id(character.id, None)
        await self.char_repo.update_current_room_id(character.id, None)
        await self.publisher.publish_regeneration(character.id)

        await self.change_location_events.publish_room_change(
            character_id=character.id,
            name=character.name,
            level=character.level,
            race=character.race.value if character.race else None,
            old_room_slug=f"house:{house_id}",
            new_room_slug=character.location_slug,
        )

        house = await self.house_repo.get_by_id(house_id)
        if house is not None:
            await self.house_events.publish(
                action="guest_left",
                house_id=house_id,
                target_user_ids=[house.owner_character_id, character.id],
                affected_character_id=character.id,
            )