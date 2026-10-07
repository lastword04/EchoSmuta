import logging
import uuid
from decimal import Decimal
from ....core.utils.exceptions import ValidationError
from ...characters.models import Character
from ...characters.adapters.mining import MiningServiceClientProtocol
from ..models import House
from ..repositories.house_furniture_repository import HouseFurnitureRepositoryProtocol
from ..repositories.house_guest_session_repository import HouseGuestSessionRepositoryProtocol
from ..repositories.house_guest_request_repository import HouseGuestRequestRepositoryProtocol
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope
from .rest_templates import RestTemplateServiceProtocol
from ..events.rest_events import RestEventsProtocol
from ..events.house_events import HouseEventsProtocol
from ...characters.events.change_location import ChangeLocationEventsProtocol

logger = logging.getLogger(__name__)



class HouseServiceProtocol:
    async def buy_house(self, character: Character) -> House: ...
    async def enter_house(self, character: Character, house_id: uuid.UUID) -> dict: ...
    async def exit_house(self, character: Character) -> None: ...
    async def get_status(self, character: Character) -> dict: ...
    async def install_furniture(self, character: Character, house_id: uuid.UUID, inventory_item_id: uuid.UUID) -> dict: ...
    async def uninstall_furniture(self, character: Character, inventory_item_id: uuid.UUID) -> dict: ...
    async def get_house_furniture(self, character: Character, house_id: uuid.UUID) -> list[dict]: ...
    async def get_my_furniture(self, character: Character) -> list[dict]: ...
    async def update_wallpaper(self, character: Character, house_id: uuid.UUID, wallpaper_photo_id: uuid.UUID | None) -> House: ...
    async def recalculate_regen(self, house_id: uuid.UUID) -> None: ...
       

class HouseService(HouseServiceProtocol):
    def __init__(
        self,
        house_repository,
        character_repository,
        publisher,
        settings,
        mining_client: MiningServiceClientProtocol,
        furniture_repository: HouseFurnitureRepositoryProtocol,
        events: RestEventsProtocol,
        template_service: RestTemplateServiceProtocol,        
        guest_session_repository: HouseGuestSessionRepositoryProtocol,
        guest_request_repository: HouseGuestRequestRepositoryProtocol,
        house_events: HouseEventsProtocol,
        change_location_events: ChangeLocationEventsProtocol,
    ):
        self.house_repo = house_repository
        self.char_repo = character_repository
        self.publisher = publisher
        self.settings = settings
        self.mining_client = mining_client
        self.furniture_repo = furniture_repository
        self.events = events
        self.template_service = template_service     
        self.guest_session_repo = guest_session_repository
        self.guest_request_repo = guest_request_repository
        self.house_events = house_events
        self.change_location_events = change_location_events

    async def buy_house(self, character: Character) -> House:
        if character.location_slug != self.settings.residential_location_slug:
            raise ValidationError(field="location", message="Персонаж должен находиться в локации Частные дома")

        price = Decimal(self.settings.house_price_ducats)
        if not await self.char_repo.subtract_ducats(character.id, price):
            raise ValidationError(field="ducats", message="Недостаточно дукатов")

        number = await self.house_repo.next_number()
        house = await self.house_repo.create(
            owner_id=character.id,
            number=number,
            location_slug=self.settings.residential_location_slug,
            capacity=self.settings.house_capacity,
        )

        try:
            city_name = self.template_service.get_city_name(house.location_slug)
            private_message = self.template_service.get_house_purchase_self_message(
                number=house.number,
                city_name=city_name,
            )
            public_message = self.template_service.get_house_purchase_public_message(
                character_name=character.name,
                number=house.number,
                city_name=city_name,
            )
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="house_purchase_private",
                    character_id=character.id,
                    location_slug=house.location_slug,
                    content=private_message,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character.id],
                )
            )
            await self.events.publish_message(
                ItemMessageEventSchema(
                    event_type="house_purchase_city",
                    character_id=character.id,
                    location_slug=house.location_slug,
                    content=public_message,
                    scope=ItemMessageScope.CITY,
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish house purchase events: {e}")

        return house

    async def enter_house(self, character: Character, house_id: uuid.UUID) -> dict:
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")
        if house.owner_character_id != character.id:
            raise ValidationError(field="house_id", message="Вы не владелец этого дома")
        if character.location_slug != house.location_slug:
            raise ValidationError(field="location", message="Персонаж должен находиться в локации Частные дома")
        if character.current_house_id == house_id:
            # Уже в доме — возвращаем payload, чтобы фронт мог синхронизировать UI.
            return await self._current_house_payload(house, character)

        await self.char_repo.update_current_house_id(character.id, house_id)
        await self.char_repo.update_current_room_id(character.id, f"house:{house_id}")
        await self.publisher.publish_regeneration(character.id)

        await self.change_location_events.publish_room_change(
            character_id=character.id,
            name=character.name,
            level=character.level,
            race=character.race.value if character.race else None,
            old_room_slug=character.location_slug,
            new_room_slug=f"house:{house_id}",
        )

        return await self._current_house_payload(house, character)

    async def exit_house(self, character: Character) -> None:
        if character.current_house_id is None:
            raise ValidationError(field="current_house_id", message="Персонаж не в доме")
        house_id = character.current_house_id

        was_guest = False
        session = await self.guest_session_repo.get_by_character(character.id)
        if session is not None and session.house_id == house_id:
            await self.guest_session_repo.delete_by_character(character.id)
            was_guest = True

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

        # Удаляем все pending-заявки на стук от этого персонажа: он покидает
        # дом, висеть в «стучится…» у владельца они не должны.
        await self.guest_request_repo.delete_by_character(character.id)

        if was_guest:
            house = await self.house_repo.get_by_id(house_id)
            if house is not None:
                await self.house_events.publish(
                    action="guest_left",
                    house_id=house_id,
                    target_user_ids=[house.owner_character_id, character.id],
                    affected_character_id=character.id,
                )

    async def get_status(self, character: Character) -> dict:
        houses = await self.house_repo.list_by_owner(character.id)

        houses_payload = []
        for h in houses:
            houses_payload.append({
                "id": str(h.id),
                "number": h.number,
                "capacity": h.capacity,
                "current_volume": h.current_volume,
                "bonuses": {
                    stat: round((mult - 1.0) * 100)
                    for stat, mult in (h.regen_multipliers or {}).items()
                },
                "wallpaper_photo_id": str(h.wallpaper_photo_id) if h.wallpaper_photo_id else None,
                "furniture": await self._furniture_payload(h),
                "guests_count": await self.guest_session_repo.count_by_house(h.id),
                "guests": await self._guests_payload(h.id),
            })

        current_house_payload = None
        if character.current_house_id is not None:
            house = await self.house_repo.get_by_id(character.current_house_id)
            if house is not None:
                current_house_payload = await self._current_house_payload(house, character)

        return {
            "location_slug": character.location_slug,
            "current_house_id": str(character.current_house_id) if character.current_house_id else None,
            "house_price": str(Decimal(self.settings.house_price_ducats)),
            "max_guests": self.settings.house_max_guests,
            "houses": houses_payload,
            "current_house": current_house_payload,
        }

    async def install_furniture(self, character: Character, house_id: uuid.UUID, inventory_item_id: uuid.UUID) -> dict:
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")
        if house.owner_character_id != character.id:
            raise ValidationError(field="house_id", message="Вы не владелец этого дома")
        if character.location_slug != house.location_slug:
            raise ValidationError(field="location", message="Персонаж должен находиться в локации Частные дома")

        existing = await self.furniture_repo.get_by_inventory_item(inventory_item_id)
        if existing is not None:
            raise ValidationError(field="inventory_item_id", message="Предмет уже установлен в дом")

        furniture_list = await self.mining_client.get_character_furniture(character.id)
        item = next((f for f in furniture_list if f.inventory_item_id == inventory_item_id), None)
        if item is None:
            raise ValidationError(field="inventory_item_id", message="Предмет не найден в инвентаре")

        if item.shop_id is not None:
            raise ValidationError(
                field="inventory_item_id",
                message="Предмет находится в лавке — сначала заберите его оттуда",
            )

        if item.volume is None:
            raise ValidationError(field="inventory_item_id", message="У предмета не указан объём")

        if house.current_volume + item.volume > house.capacity:
            raise ValidationError(field="capacity", message="Недостаточно места в доме")

        await self.furniture_repo.install(house_id=house_id, inventory_item_id=inventory_item_id)
        await self._recalculate_house_regen(house_id, character.id)
        
        new_weight = character.weight - item.weight
        await self.char_repo.update_weight(character.id, float(new_weight))

        guests = await self.guest_session_repo.list_by_house(house_id)
        await self.house_events.publish(
            action="furniture_changed",
            house_id=house_id,
            target_user_ids=[house.owner_character_id] + [s.character_id for s in guests],
            affected_character_id=house.owner_character_id,
        )

        return {
            "house_id": house_id,
            "my_furniture": await self.get_my_furniture(character),
            "house_furniture": await self.get_house_furniture(character, house_id),
            "house": await self._house_payload(await self.house_repo.get_by_id(house_id)),
        }

    async def uninstall_furniture(self, character: Character, inventory_item_id: uuid.UUID) -> dict:
        furniture = await self.furniture_repo.get_by_inventory_item(inventory_item_id)
        if furniture is None:
            raise ValidationError(field="inventory_item_id", message="Предмет не установлен")

        house = await self.house_repo.get_by_id(furniture.house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")
        if house.owner_character_id != character.id:
            raise ValidationError(field="house_id", message="Вы не владелец этого дома")

        furniture_list = await self.mining_client.get_character_furniture(character.id)
        item = next((f for f in furniture_list if f.inventory_item_id == inventory_item_id), None)
        if item is None:
            raise ValidationError(field="inventory_item_id", message="Предмет не найден в инвентаре")

        bonuses = character.equipment_bonuses or {}
        max_weight = character.max_weight + bonuses.get("max_weight_bonus", 0)
        if character.weight + item.weight > max_weight:
            raise ValidationError(
                field="weight",
                message="У вас нет места в рюкзаке",
            )

        await self.furniture_repo.uninstall(inventory_item_id)
        await self._recalculate_house_regen(house.id, character.id)

        new_weight = character.weight + item.weight
        await self.char_repo.update_weight(character.id, float(new_weight))

        guests = await self.guest_session_repo.list_by_house(house.id)
        await self.house_events.publish(
            action="furniture_changed",
            house_id=house.id,
            target_user_ids=[house.owner_character_id] + [s.character_id for s in guests],
            affected_character_id=house.owner_character_id,
        )

        return {
            "house_id": house.id,
            "my_furniture": await self.get_my_furniture(character),
            "house_furniture": await self.get_house_furniture(character, house.id),
            "house": await self._house_payload(await self.house_repo.get_by_id(house.id)),
        }

    async def _recalculate_house_regen(self, house_id: uuid.UUID, character_id: uuid.UUID) -> None:
        furniture_records = await self.furniture_repo.list_by_house(house_id)
        if not furniture_records:
            await self.house_repo.set_current_volume(house_id, 0)
            await self.house_repo.set_regen_multipliers(house_id, {"health": 1.0, "mana": 1.0, "tiredness": 1.0})
            return

        furniture_list = await self.mining_client.get_character_furniture(character_id)
        items_by_id = {f.inventory_item_id: f for f in furniture_list}

        total_volume = 0
        bonuses = {"health": 0.0, "mana": 0.0, "tiredness": 0.0}

        slug_groups: dict[str, list] = {}
        for record in furniture_records:
            item = items_by_id.get(record.inventory_item_id)
            if item is None:
                continue
            if item.volume is not None:
                total_volume += item.volume
            if item.max_wear is not None and item.wear >= item.max_wear:
                continue
            if item.slug not in slug_groups:
                slug_groups[item.slug] = []
            slug_groups[item.slug].append(item)

        for slug, items in slug_groups.items():
            for idx, item in enumerate(items):
                params = item.ability_parameters or {}
                if idx == 0:
                    bonuses["health"] += params.get("health_percentage", 0.0)
                    bonuses["mana"] += params.get("mana_percentage", 0.0)
                    bonuses["tiredness"] += params.get("tiredness_percentage", 0.0)
                else:
                    bonuses["health"] += params.get("health_percentage_weared", 0.0)
                    bonuses["mana"] += params.get("mana_percentage_weared", 0.0)
                    bonuses["tiredness"] += params.get("tiredness_percentage_weared", 0.0)

        multipliers = {
            "health": 1.0 + bonuses["health"],
            "mana": 1.0 + bonuses["mana"],
            "tiredness": 1.0 + bonuses["tiredness"],
        }

        await self.house_repo.set_current_volume(house_id, total_volume)
        await self.house_repo.set_regen_multipliers(house_id, multipliers)

    async def recalculate_regen(self, house_id: uuid.UUID) -> None:
        """Публичный пересчёт множителей регенерации дома для фоновых задач."""
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            return
        await self._recalculate_house_regen(house_id, house.owner_character_id)

    async def get_house_furniture(self, character: Character, house_id: uuid.UUID) -> list[dict]:
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")
        is_owner = house.owner_character_id == character.id
        is_guest = character.current_house_id == house.id
        if not is_owner and not is_guest:
            raise ValidationError(field="house_id", message="Вы не владелец и не гость этого дома")

        furniture_records = await self.furniture_repo.list_by_house(house_id)
        if not furniture_records:
            return []

        furniture_list = await self.mining_client.get_character_furniture(house.owner_character_id)
        items_by_id = {f.inventory_item_id: f for f in furniture_list}

        result = []
        for record in furniture_records:
            item = items_by_id.get(record.inventory_item_id)
            if item is None:
                continue
            result.append({
                "house_id": house_id,
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

    async def get_my_furniture(self, character: Character) -> list[dict]:
        furniture_list = await self.mining_client.get_character_furniture(character.id)
        if not furniture_list:
            return []

        houses = await self.house_repo.list_by_owner(character.id)
        installed_ids = set()
        for house in houses:
            records = await self.furniture_repo.list_by_house(house.id)
            installed_ids.update(r.inventory_item_id for r in records)

        result = []
        for item in furniture_list:
            if item.inventory_item_id in installed_ids:
                continue
            result.append({
                "house_id": None,
                "inventory_item_id": item.inventory_item_id,
                "slug": item.slug,
                "wear": item.wear,
                "max_wear": item.max_wear,
                "volume": item.volume,
                "weight": item.weight,
                "ability_parameters": item.ability_parameters,
                "name": item.name,
            })
        return result

    async def update_wallpaper(self, character: Character, house_id: uuid.UUID, wallpaper_photo_id: uuid.UUID | None) -> House:
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            raise ValidationError(field="house_id", message="Дом не найден")
        if house.owner_character_id != character.id:
            raise ValidationError(field="house_id", message="Вы не владелец этого дома")
        
        await self.house_repo.set_wallpaper_photo_id(house_id, wallpaper_photo_id)
        guests = await self.guest_session_repo.list_by_house(house_id)
        await self.house_events.publish(
            action="wallpaper_changed",
            house_id=house_id,
            target_user_ids=[house.owner_character_id] + [s.character_id for s in guests],
            affected_character_id=house.owner_character_id,
        )
        return await self.house_repo.get_by_id(house_id)

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

    async def _current_house_payload(self, house: House, character: Character) -> dict:
        """Полный payload дома для текущего персонажа (та же форма, что в get_status)."""
        is_owner = house.owner_character_id == character.id
        if is_owner:
            owner_name = character.name
        else:
            owner = await self.char_repo.get(house.owner_character_id)
            owner_name = owner.name if owner is not None else "—"
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

    async def _house_payload(self, house: House) -> dict:
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
            "guests_count": await self.guest_session_repo.count_by_house(house.id),
            "guests": await self._guests_payload(house.id),
        }             