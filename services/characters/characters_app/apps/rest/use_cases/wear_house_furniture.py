import logging
import uuid

import sqlalchemy as sa
from typing import Protocol
from typing_extensions import Self

from ....core.use_cases import UseCaseProtocol
from ...characters.adapters.mining import MiningServiceClientProtocol
from ...characters.models import Character
from ..events.house_events import HouseEventsProtocol
from ..models import HouseFurniture
from ..repositories.house_furniture_repository import HouseFurnitureRepositoryProtocol
from ..repositories.house_guest_session_repository import HouseGuestSessionRepositoryProtocol
from ..repositories.house_repository import HouseRepositoryProtocol
from ..repositories.inventory_item_work_accumulator_repository import (
    InventoryItemWorkAccumulatorRepositoryProtocol,
)
from ..services.house_service import HouseServiceProtocol

logger = logging.getLogger(__name__)


class WearHouseFurnitureUseCaseProtocol(UseCaseProtocol[int]):
    async def __call__(self: Self) -> int: ...


class WearHouseFurnitureUseCase(WearHouseFurnitureUseCaseProtocol):
    """
    Тик износа мебели в домах.

    1. Собирает обитателей домов (current_house_id) и их неполные статы.
    2. Собирает мебель этих домов и читает её из mining пачкой.
    3. Начисляет минуты работы в аккумулятор: +1 обитатель-пользователь за тик.
    4. Конвертирует накопленное в wear (ставка минут из settings).
    5. При поломке предмета пересчитывает regen_multipliers дома и шлёт событие.
    """

    def __init__(
        self: Self,
        session,
        settings,
        mining_client: MiningServiceClientProtocol,
        accumulator_repository: InventoryItemWorkAccumulatorRepositoryProtocol,
        furniture_repository: HouseFurnitureRepositoryProtocol,
        house_repository: HouseRepositoryProtocol,
        guest_session_repository: HouseGuestSessionRepositoryProtocol,
        house_service: HouseServiceProtocol,
        house_events: HouseEventsProtocol,
    ):
        self.session = session
        self.settings = settings
        self.mining_client = mining_client
        self.accumulator_repo = accumulator_repository
        self.furniture_repo = furniture_repository
        self.house_repo = house_repository
        self.guest_session_repo = guest_session_repository
        self.house_service = house_service
        self.house_events = house_events

    async def __call__(self: Self) -> int:
        occupants_by_house = await self._collect_occupants()
        if not occupants_by_house:
            return 0

        items_by_house, all_item_ids = await self._collect_furniture(list(occupants_by_house))
        if not all_item_ids:
            return 0

        mining_items = await self.mining_client.get_furniture_bulk(all_item_ids)
        item_by_id = {i.inventory_item_id: i for i in mining_items}

        tick_minutes = self.settings.house_wear_tick_seconds / 60.0
        additions = self._count_work(occupants_by_house, items_by_house, item_by_id, tick_minutes)
        if not additions:
            return 0

        entries = await self._accumulate_and_convert(additions)
        if not entries:
            return len(additions)

        broken_ids = await self.mining_client.add_furniture_wear_bulk(entries)
        if broken_ids:
            for house_id in self._houses_for_items(broken_ids, items_by_house):
                await self.house_service.recalculate_regen(house_id)
            logger.info(f"House furniture wear: broken items {broken_ids}")

        for house_id in self._houses_for_items([item_id for item_id, _ in entries], items_by_house):
            await self._publish_house_update(house_id)

        return len(additions)

    async def _collect_occupants(self) -> dict[uuid.UUID, list[set[str]]]:
        """Обитатели домов + множество неполных статов каждого."""
        result = await self.session.execute(
            sa.select(
                Character.id,
                Character.current_house_id,
                Character.health,
                Character.max_health,
                Character.mana,
                Character.max_mana,
                Character.tiredness,
                Character.equipment_bonuses,
            ).where(
                Character.current_house_id.isnot(None),
                Character.is_active == True,
                Character.is_banned == False,
            )
        )
        occupants: dict[uuid.UUID, list[set[str]]] = {}
        for row in result.all():
            bonuses = row.equipment_bonuses or {}
            incomplete: set[str] = set()
            if row.health < row.max_health + bonuses.get("max_health_bonus", 0):
                incomplete.add("health")
            if row.mana < row.max_mana + bonuses.get("max_mana_bonus", 0):
                incomplete.add("mana")
            if row.tiredness > 0:
                incomplete.add("tiredness")
            occupants.setdefault(row.current_house_id, []).append(incomplete)
        return occupants

    async def _collect_furniture(self, house_ids: list[uuid.UUID]) -> tuple[dict[uuid.UUID, list[uuid.UUID]], list[uuid.UUID]]:
        result = await self.session.execute(
            sa.select(HouseFurniture.house_id, HouseFurniture.inventory_item_id).where(
                HouseFurniture.house_id.in_(house_ids)
            )
        )
        items_by_house: dict[uuid.UUID, list[uuid.UUID]] = {}
        all_ids: list[uuid.UUID] = []
        for row in result.all():
            items_by_house.setdefault(row.house_id, []).append(row.inventory_item_id)
            all_ids.append(row.inventory_item_id)
        return items_by_house, all_ids

    def _count_work(
        self,
        occupants_by_house: dict[uuid.UUID, list[set[str]]],
        items_by_house: dict[uuid.UUID, list[uuid.UUID]],
        item_by_id: dict,
        tick_minutes: float,
    ) -> dict[uuid.UUID, float]:
        additions: dict[uuid.UUID, float] = {}
        for house_id, item_ids in items_by_house.items():
            occupants = occupants_by_house.get(house_id, [])
            for item_id in item_ids:
                item = item_by_id.get(item_id)
                if item is None:
                    continue
                if item.max_wear is None or item.wear >= item.max_wear:
                    continue
                stats = self._item_regen_stats(item.ability_parameters or {})
                if not stats:
                    continue
                working = sum(1 for incomplete in occupants if stats & incomplete)
                if working:
                    additions[item_id] = working * tick_minutes
        return additions

    @staticmethod
    def _item_regen_stats(params: dict) -> set[str]:
        stats: set[str] = set()
        if params.get("health_percentage") or params.get("health_percentage_weared"):
            stats.add("health")
        if params.get("mana_percentage") or params.get("mana_percentage_weared"):
            stats.add("mana")
        if params.get("tiredness_percentage") or params.get("tiredness_percentage_weared"):
            stats.add("tiredness")
        return stats

    async def _accumulate_and_convert(self, additions: dict[uuid.UUID, float]) -> list[tuple[uuid.UUID, int]]:
        rate = self.settings.house_wear_rate_minutes
        entries: list[tuple[uuid.UUID, int]] = []
        for item_id, minutes in additions.items():
            await self.accumulator_repo.add_work_minutes(item_id, minutes)
            accumulated = await self.accumulator_repo.get_accumulated(item_id)
            if accumulated >= rate:
                wear_add = int(accumulated // rate)
                await self.accumulator_repo.subtract_work_minutes(item_id, wear_add * rate)
                entries.append((item_id, wear_add))
        return entries

    @staticmethod
    def _houses_for_items(
        item_ids: list[uuid.UUID],
        items_by_house: dict[uuid.UUID, list[uuid.UUID]],
    ) -> set[uuid.UUID]:
        house_by_item: dict[uuid.UUID, uuid.UUID] = {
            item_id: house_id
            for house_id, ids in items_by_house.items()
            for item_id in ids
        }
        return {house_by_item[i] for i in item_ids if i in house_by_item}

    async def _publish_house_update(self, house_id: uuid.UUID) -> None:
        """Сообщить владельцу и гостям, что мебель дома изменилась (износ/поломка)."""
        house = await self.house_repo.get_by_id(house_id)
        if house is None:
            return
        guests = await self.guest_session_repo.list_by_house(house_id)
        await self.house_events.publish(
            action="furniture_changed",
            house_id=house_id,
            target_user_ids=[house.owner_character_id] + [s.character_id for s in guests],
        )