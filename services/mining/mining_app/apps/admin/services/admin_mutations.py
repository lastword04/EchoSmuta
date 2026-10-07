import logging
import uuid
from decimal import Decimal
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.utils.exceptions import ValidationError
from ....settings import Settings
from ...items.adapters.characters import CharacterServiceClientProtocol
from ...items.schemas import InventoryItemCreateSchema
from ...items.services.character.character_items import CharacterItemServiceProtocol
from ...items.services.character.equipment import EquipmentServiceProtocol
from ...resources.events.publisher import RedisPublisherProtocol
from ...resources.services.character_resource import CharacterResourceServiceProtocol
from ..repositories.admin_mutations import AdminMutationRepository
from ..schemas import (
    AdminGiveItemSchema,
    AdminLogListSchema,
    AdminMoneyAddSchema,
    AdminMoneySetSchema,
    AdminMutationResultSchema,
    AdminResourceMutationSchema,
    AdminTakeItemSchema,
)

logger = logging.getLogger(__name__)


class AdminMutationServiceProtocol(Protocol):
    async def give_item(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminGiveItemSchema) -> AdminMutationResultSchema: ...
    async def take_item(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminTakeItemSchema) -> AdminMutationResultSchema: ...
    async def give_resource(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminResourceMutationSchema) -> AdminMutationResultSchema: ...
    async def take_resource(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminResourceMutationSchema) -> AdminMutationResultSchema: ...
    async def add_money(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminMoneyAddSchema) -> AdminMutationResultSchema: ...
    async def set_money(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminMoneySetSchema) -> AdminMutationResultSchema: ...
    async def list_logs(self, character_id: uuid.UUID | None, limit: int, offset: int) -> AdminLogListSchema: ...


class AdminMutationService(AdminMutationServiceProtocol):
    def __init__(
        self,
        repository: AdminMutationRepository,
        item_service: CharacterItemServiceProtocol,
        equipment_service: EquipmentServiceProtocol,
        resource_service: CharacterResourceServiceProtocol,
        characters: CharacterServiceClientProtocol,
        publisher: RedisPublisherProtocol,
        settings: Settings,
    ):
        self.repository = repository
        self.item_service = item_service
        self.equipment_service = equipment_service
        self.resource_service = resource_service
        self.characters = characters
        self.publisher = publisher
        self.settings = settings

    async def give_item(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminGiveItemSchema) -> AdminMutationResultSchema:
        if data.amount > self.settings.admin.max_stack:
            raise ValidationError(field="amount", message=f"Amount cannot exceed {self.settings.admin.max_stack}")
        
        # Сначала мутация
        await self.item_service.add_item(character_id, InventoryItemCreateSchema(**data.model_dump(exclude={"reason"})))
        
        # Потом лог (если мутация упала — сюда не дойдём)
        details = data.model_dump(mode="json")
        await self._log(admin.user_id, character_id, "give_item", details)
        
        await self._publish(character_id, "give")
        return AdminMutationResultSchema(action="give", character_id=character_id, details=details)


    async def take_item(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminTakeItemSchema) -> AdminMutationResultSchema:
        # Сначала мутация
        await self.item_service.take_item(
            character_id=character_id, 
            **data.model_dump(exclude={"reason"})
        )
        if data.force:
            await self.equipment_service.refresh_bonuses(character_id)
        
        # Потом лог
        details = data.model_dump(mode="json", exclude_none=True)
        await self._log(admin.user_id, character_id, "take_item", details)
        
        await self._publish(character_id, "take")
        return AdminMutationResultSchema(action="take", character_id=character_id, details=details)


    async def give_resource(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminResourceMutationSchema) -> AdminMutationResultSchema:
        await self.resource_service.increment_amount(character_id, data.resource_slug, data.amount)
        
        details = data.model_dump(mode="json")
        await self._log(admin.user_id, character_id, "give_resource", details)
        
        await self._publish(character_id, "give")
        return AdminMutationResultSchema(action="give", character_id=character_id, details=details)


    async def take_resource(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminResourceMutationSchema) -> AdminMutationResultSchema:
        resource = await self.resource_service.get_by_character_and_resource(character_id, data.resource_slug)
        if resource is None or resource.amount < data.amount:
            raise ValidationError(field="amount", message="Character does not own enough resources")
        
        await self.resource_service.decrement_amount(character_id, data.resource_slug, data.amount)
        
        details = data.model_dump(mode="json")
        await self._log(admin.user_id, character_id, "take_resource", details)
        
        await self._publish(character_id, "take")
        return AdminMutationResultSchema(action="take", character_id=character_id, details=details)


    async def add_money(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminMoneyAddSchema) -> AdminMutationResultSchema:
        await self._change_money(character_id, data.currency, data.amount, credit=True)
        
        details = data.model_dump(mode="json")
        await self._log(admin.user_id, character_id, "money_add", details)
        
        await self._publish(character_id, "money_add")
        return AdminMutationResultSchema(action="money_add", character_id=character_id, details=details)


    async def set_money(self, admin: UserTokenDataReadSchema, character_id: uuid.UUID, data: AdminMoneySetSchema) -> AdminMutationResultSchema:
        character = await self.characters.get_full_character(character_id)
        delta = data.amount - getattr(character, data.currency)
        if delta:
            await self._change_money(character_id, data.currency, abs(delta), credit=delta > 0)
        
        details = data.model_dump(mode="json")
        await self._log(admin.user_id, character_id, "money_set", details)
        
        await self._publish(character_id, "money_set")
        return AdminMutationResultSchema(action="money_set", character_id=character_id, details=details)

    async def list_logs(self, character_id: uuid.UUID | None, limit: int, offset: int) -> AdminLogListSchema:
        logs, count = await self.repository.list_logs(character_id, limit, offset)
        return AdminLogListSchema(objects=logs, count=count)

    async def _log(self, admin_user_id: uuid.UUID, character_id: uuid.UUID, action: str, details: dict) -> None:
        await self.repository.create_log(admin_user_id, character_id, action, details)

    async def _change_money(self, character_id: uuid.UUID, currency: str, amount: Decimal, credit: bool) -> None:
        operation_id = uuid.uuid4()
        operation_type = "admin_credit" if credit else "admin_debit"
        if currency == "ducats":
            method = self.characters.credit_ducats if credit else self.characters.debit_ducats
            await method(character_id, amount, operation_id=operation_id, operation_type=operation_type, source="admin", item_meta={})
            return
        method = self.characters.credit_gold if credit else self.characters.debit_gold
        await method(character_id, amount, operation_id=operation_id, operation_type=operation_type, source="admin", item_meta={})

    async def _publish(self, character_id: uuid.UUID, action: str) -> None:
        try:
            await self.publisher.publish(
                f"inventory:invalidation:{character_id}",
                {"action": action, "tags": ["Inventory", "ShopItems", "Resources"]},
            )
        except Exception:
            logger.warning("Unable to publish admin invalidation for character %s", character_id, exc_info=True)
