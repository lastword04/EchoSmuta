import logging
import math
import uuid
from typing import Protocol, Self

from .....core.utils.exceptions import ValidationError
from ...adapters.characters import CharacterServiceClientProtocol
from ...enums import EquipmentSlot, ItemType
from ...repositories.character.character_equipment import (
    CharacterEquipmentRepositoryProtocol,
)
from ...repositories.character.character_items import CharacterItemRepositoryProtocol
from ...schemas import CharacterEquipmentReadSchema, InventoryItemReadSchema
from ...services.items.items_component import ItemComponentServiceProtocol

logger = logging.getLogger(__name__)

ITEM_SLOT_MAP = {
    ItemType.HELMET: EquipmentSlot.HEAD,
    ItemType.ARMOR: EquipmentSlot.CHEST,
    ItemType.GAUNTLETS: EquipmentSlot.HANDS,
    ItemType.GLOVES: EquipmentSlot.GLOVES,
    ItemType.LEGGINGS: EquipmentSlot.LEGS,
    ItemType.BOOTS: EquipmentSlot.FEET,
    ItemType.WEAPON: EquipmentSlot.WEAPON,
    ItemType.SHIELD: EquipmentSlot.SHIELD,
    ItemType.CLOAK: EquipmentSlot.CLOAK,
    ItemType.AMULET: EquipmentSlot.AMULET,
    ItemType.PENDANT: EquipmentSlot.PENDANT,
}

# Слоты полного комплекта брони (плащ взаимоисключающ с ними)
ARMOR_SLOTS = {
    EquipmentSlot.HEAD,
    EquipmentSlot.CHEST,
    EquipmentSlot.HANDS,
    EquipmentSlot.GLOVES,
    EquipmentSlot.LEGS,
    EquipmentSlot.FEET,
}

SLOT_LABELS = {
    EquipmentSlot.HEAD: "шлем",
    EquipmentSlot.CHEST: "доспех",
    EquipmentSlot.HANDS: "нарукавники",
    EquipmentSlot.GLOVES: "перчатки",
    EquipmentSlot.LEGS: "поножи",
    EquipmentSlot.FEET: "обувь",
}


class EquipmentServiceProtocol(Protocol):
    async def equip(self: Self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> CharacterEquipmentReadSchema: ...
    async def unequip(self: Self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> None: ...
    async def repair(self: Self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> InventoryItemReadSchema: ...
    async def is_equipped(self: Self, inventory_item_id: uuid.UUID) -> bool: ...
    async def get_equipment_bonuses(self: Self, character_id: uuid.UUID) -> dict: ...
    async def get_equipped_items(self: Self, character_id: uuid.UUID) -> list[InventoryItemReadSchema]: ...
    async def refresh_bonuses(self: Self, character_id: uuid.UUID) -> None: ...


class EquipmentService(EquipmentServiceProtocol):
    def __init__(
        self,
        equipment_repository: CharacterEquipmentRepositoryProtocol,
        character_item_repository: CharacterItemRepositoryProtocol,
        character_service: CharacterServiceClientProtocol,
        item_component_service: ItemComponentServiceProtocol,
    ):
        self.equipment_repository = equipment_repository
        self.character_item_repository = character_item_repository
        self.character_service = character_service
        self.item_component_service = item_component_service

    async def equip(self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> CharacterEquipmentReadSchema:
        inventory_item = await self.character_item_repository.get_by_id_and_character(inventory_item_id, character_id)
        item = inventory_item.item
        if item.item_type == ItemType.RING:
            slot = await self.equipment_repository.get_first_free_ring_slot(character_id) or EquipmentSlot.RING1
        else:
            slot = ITEM_SLOT_MAP.get(item.item_type)
        if slot is None:
            raise ValidationError(field="item_type", message="Item cannot be equipped")

        character = await self.character_service.get_character_for_requirements(character_id)
        parameters = item.parameters or {}
        requirements = {
            "level": item.minimal_level,
            "strength": parameters.get("required_strength", 0),
            "agility": parameters.get("required_agility", 0),
            "luck": parameters.get("required_luck", 0),
        }
        actual = {
            "level": character.level,
            "strength": character.eff_power,
            "agility": character.eff_agility,
            "luck": character.eff_lucky,
        }
        failed = {key: {"required": value, "actual": actual[key]} for key, value in requirements.items() if actual[key] < value}
        if failed:
            raise ValidationError(field=list(failed), message=f"Character does not meet equipment requirements: {failed}")

        # ═══ ВЗАИМОИСКЛЮЧЕНИЕ: плащ ↔ полный комплект брони ═══
        equipped = await self.equipment_repository.get_all_by_character(character_id)
        occupied_slots = {eq.slot for eq in equipped}

        if slot == EquipmentSlot.CLOAK:
            armor_on = [SLOT_LABELS[s] for s in (
                EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS,
                EquipmentSlot.GLOVES, EquipmentSlot.LEGS, EquipmentSlot.FEET,
            ) if s in occupied_slots]
            if armor_on:
                raise ValidationError(
                    field="slot",
                    message="Сначала снимите " + ", ".join(armor_on),
                )
        elif slot in ARMOR_SLOTS:
            if EquipmentSlot.CLOAK in occupied_slots:
                raise ValidationError(
                    field="slot",
                    message="Сначала снимите плащ",
                )

        
        result = await self.equipment_repository.equip(character_id, inventory_item_id, slot)
        await self._recalculate_and_send_bonuses(character_id)
        return result

    async def unequip(self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> None:
        if not await self.equipment_repository.unequip_by_inventory_item(character_id, inventory_item_id):
            raise ValidationError(field="inventory_item_id", message="Предмет не надет")
        await self._recalculate_and_send_bonuses(character_id)

    async def repair(self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> InventoryItemReadSchema:
        inventory_item = await self.character_item_repository.get_by_id_and_character(inventory_item_id, character_id)
        components = await self.item_component_service.get_components_with_resource_names(inventory_item.item_slug)
        if not components:
            raise ValidationError(field="item_slug", message="Item has no repairable components")
        repair_costs_by_resource = {}
        for component in components:
            repair_costs_by_resource.setdefault(
                component.resource_slug,
                {"quantity": 0, "name": component.resource_name},
            )["quantity"] += math.ceil(component.quantity / 2)
        repair_costs = [
            (resource_slug, cost["quantity"], cost["name"])
            for resource_slug, cost in repair_costs_by_resource.items()
        ]
        return await self.equipment_repository.repair_item(character_id, inventory_item_id, repair_costs)

    async def is_equipped(self, inventory_item_id: uuid.UUID) -> bool:
        return await self.equipment_repository.get_by_inventory_item(inventory_item_id) is not None

    async def get_equipment_bonuses(self, character_id: uuid.UUID) -> dict:
        """
        Получает суммарные бонусы от всей экипировки персонажа.
        
        Извлекает бонусы из ability_parameters (статы, проценты, магия) 
        и parameters (боевые параметры), суммирует их.
        
        Возвращает словарь вида:
        {
            "strength": 10,           # из ability_parameters
            "agility": 5,             # из ability_parameters
            "luck": 3,                # из ability_parameters
            "health": 100,            # из ability_parameters
            "mana": 50,               # из ability_parameters
            "strength_percent": 0.15, # из ability_parameters
            "defense": 20,            # из parameters
            "damage_min": 10,         # из parameters
            "damage_max": 15,         # из parameters
            "dodge_self": 0.25,       # из parameters
            "crit_self": 0.10,        # из parameters
            "dodge_reduction": -0.20, # из parameters
            "crit_reduction": -0.15,  # из parameters
            "magic_order_1_self": 0.35, # из ability_parameters
        }
        """
        from ...utils.bonus_mapper import extract_bonuses_from_item
        
        equipment_items = await self.equipment_repository.get_all_by_character(character_id)
        bonuses = {}
        
        for eq_item in equipment_items:
            inventory_item = await self.character_item_repository.get_by_id(eq_item.inventory_item_id)
            if not inventory_item or not inventory_item.item:
                continue
            
            # Извлекаем бонусы из parameters и ability_parameters
            item_bonuses = extract_bonuses_from_item(
                inventory_item.item.parameters,
                inventory_item.item.ability_parameters
            )
            
            # Суммируем бонусы
            for key, value in item_bonuses.items():
                bonuses[key] = bonuses.get(key, 0) + value
        
        return bonuses

    async def get_equipped_items(self: Self, character_id: uuid.UUID) -> list[InventoryItemReadSchema]:
        """Получить все экипированные предметы персонажа"""
        from ...schemas import InventoryItemReadSchema, ItemReadSchema
        
        equipment_items = await self.equipment_repository.get_all_by_character(character_id)
        result = []
        for eq_item in equipment_items:
            inventory_item = await self.character_item_repository.get_by_id(eq_item.inventory_item_id)
            if inventory_item and inventory_item.item:
                item_dict = {k: v for k, v in inventory_item.__dict__.items() if k != 'item' and not k.startswith('_')}
                result.append(InventoryItemReadSchema(
                    **item_dict,
                    item=ItemReadSchema.model_validate(inventory_item.item, from_attributes=True)
                ))
        return result

    async def refresh_bonuses(self: Self, character_id: uuid.UUID) -> None:
        await self._recalculate_and_send_bonuses(character_id)

    async def _recalculate_and_send_bonuses(self, character_id: uuid.UUID):
        try:
            bonuses = await self.get_equipment_bonuses(character_id)
            await self.character_service.recalculate_equipment_bonuses(character_id, bonuses)
        except Exception:
            logger.exception(f"Failed to recalculate equipment bonuses for character {character_id}")
