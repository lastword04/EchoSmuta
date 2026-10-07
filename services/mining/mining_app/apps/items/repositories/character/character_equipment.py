import uuid
from typing import Protocol, Self

import sqlalchemy as sa
from sqlalchemy.orm import joinedload

from .....core.db import AsyncSession
from .....core.utils.exceptions import ModelNotFoundException, ValidationError
from ....resources.models import CharacterResource
from ...enums import EquipmentSlot
from ...exceptions import InsufficientResourcesForCraftingError
from ...models import CharacterEquipment, InventoryItem
from ...schemas import (
    CharacterEquipmentReadSchema,
    InventoryItemReadSchema,
    ItemReadSchema,
)


class CharacterEquipmentRepositoryProtocol(Protocol):
    async def get_by_inventory_item(self: Self, inventory_item_id: uuid.UUID) -> CharacterEquipmentReadSchema | None: ...
    async def get_by_slot(self: Self, character_id: uuid.UUID, slot: EquipmentSlot) -> CharacterEquipmentReadSchema | None: ...
    async def get_first_free_ring_slot(self: Self, character_id: uuid.UUID) -> EquipmentSlot | None: ...
    async def equip(self: Self, character_id: uuid.UUID, inventory_item_id: uuid.UUID, slot: EquipmentSlot) -> CharacterEquipmentReadSchema: ...
    async def unequip_by_inventory_item(self: Self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> bool: ...
    async def unequip_slot(self: Self, character_id: uuid.UUID, slot: EquipmentSlot) -> bool: ...
    async def repair_item(self: Self, character_id: uuid.UUID, inventory_item_id: uuid.UUID, repair_costs: list[tuple[str, int, str]]) -> InventoryItemReadSchema: ...
    async def get_all_by_character(self: Self, character_id: uuid.UUID) -> list[CharacterEquipment]: ...


class CharacterEquipmentRepository(CharacterEquipmentRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_inventory_item(self, inventory_item_id: uuid.UUID) -> CharacterEquipmentReadSchema | None:
        async with self.session as session:
            statement = sa.select(CharacterEquipment).where(CharacterEquipment.inventory_item_id == inventory_item_id)
            model = (await session.execute(statement)).scalar_one_or_none()
            return CharacterEquipmentReadSchema.model_validate(model, from_attributes=True) if model else None

    async def get_by_slot(self, character_id: uuid.UUID, slot: EquipmentSlot) -> CharacterEquipmentReadSchema | None:
        async with self.session as session:
            statement = sa.select(CharacterEquipment).where(
                CharacterEquipment.character_id == character_id,
                CharacterEquipment.slot == slot,
            )
            model = (await session.execute(statement)).scalar_one_or_none()
            return CharacterEquipmentReadSchema.model_validate(model, from_attributes=True) if model else None

    async def get_first_free_ring_slot(self, character_id: uuid.UUID) -> EquipmentSlot | None:
        async with self.session as session:
            statement = sa.select(CharacterEquipment.slot).where(
                CharacterEquipment.character_id == character_id,
                CharacterEquipment.slot.in_([EquipmentSlot.RING1, EquipmentSlot.RING2, EquipmentSlot.RING3]),
            )
            occupied = set((await session.execute(statement)).scalars().all())
            for slot in (EquipmentSlot.RING1, EquipmentSlot.RING2, EquipmentSlot.RING3):
                if slot not in occupied:
                    return slot
            return None

    async def equip(self, character_id: uuid.UUID, inventory_item_id: uuid.UUID, slot: EquipmentSlot) -> CharacterEquipmentReadSchema:
        async with self.session as session, session.begin():
            await session.execute(
                sa.delete(CharacterEquipment).where(
                    CharacterEquipment.character_id == character_id,
                    CharacterEquipment.slot == slot,
                )
            )
            await session.execute(
                sa.delete(CharacterEquipment).where(CharacterEquipment.inventory_item_id == inventory_item_id)
            )
            statement = sa.insert(CharacterEquipment).values(
                character_id=character_id,
                inventory_item_id=inventory_item_id,
                slot=slot,
            ).returning(CharacterEquipment)
            model = (await session.execute(statement)).scalar_one()
            return CharacterEquipmentReadSchema.model_validate(model, from_attributes=True)

    async def unequip_by_inventory_item(self, character_id: uuid.UUID, inventory_item_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(CharacterEquipment).where(
                    CharacterEquipment.character_id == character_id,
                    CharacterEquipment.inventory_item_id == inventory_item_id,
                )
            )
            return result.rowcount > 0

    async def unequip_slot(self, character_id: uuid.UUID, slot: EquipmentSlot) -> bool:
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(CharacterEquipment).where(
                    CharacterEquipment.character_id == character_id,
                    CharacterEquipment.slot == slot,
                )
            )
            return result.rowcount > 0

    async def repair_item(
        self,
        character_id: uuid.UUID,
        inventory_item_id: uuid.UUID,
        repair_costs: list[tuple[str, int, str]],
    ) -> InventoryItemReadSchema:
        async with self.session as session, session.begin():
            item_statement = (
                sa.select(InventoryItem)
                .options(joinedload(InventoryItem.item))
                .where(
                    InventoryItem.id == inventory_item_id,
                    InventoryItem.character_id == character_id,
                )
                .with_for_update()
            )
            inventory_item = (await session.execute(item_statement)).scalar_one_or_none()
            if inventory_item is None:
                raise ModelNotFoundException(InventoryItem, inventory_item_id)
            if not inventory_item.wear or inventory_item.wear <= 0:
                raise ValidationError(field="wear", message="Item does not require repair")

            missing_resources = {}
            locked_resources = {}
            for resource_slug, quantity, resource_name in sorted(repair_costs):
                resource_statement = (
                    sa.select(CharacterResource)
                    .where(
                        CharacterResource.character_id == character_id,
                        CharacterResource.resource_slug == resource_slug,
                    )
                    .with_for_update()
                )
                resource = (await session.execute(resource_statement)).scalar_one_or_none()
                if resource is None or resource.amount < quantity:
                    missing_resources[resource_name] = {
                        "required": quantity,
                        "current": resource.amount if resource else 0,
                    }
                else:
                    locked_resources[resource_slug] = resource

            if missing_resources:
                raise InsufficientResourcesForCraftingError(missing_resources=missing_resources)

            for resource_slug, quantity, _ in repair_costs:
                locked_resources[resource_slug].amount -= quantity
            inventory_item.wear = 0
            await session.flush()

            return InventoryItemReadSchema(
                **{
                    key: value
                    for key, value in inventory_item.__dict__.items()
                    if key != "item" and not key.startswith("_")
                },
                item=ItemReadSchema.model_validate(inventory_item.item, from_attributes=True),
            )

    async def get_all_by_character(self, character_id: uuid.UUID) -> list[CharacterEquipment]:
        """Получить все экипированные предметы персонажа."""
        async with self.session as session:
            statement = sa.select(CharacterEquipment).where(
                CharacterEquipment.character_id == character_id
            )
            result = await session.execute(statement)
            return list(result.scalars().all())
