"""Валидатор допуска персонажа к крафту предмета (async-версия).

Логика выделена из ``CreateItemsCreatingActionService``: проверки уровня,
усталости, локации/лицензии и наличия ресурсов ранее дублировались в
``create_new_item_crafting_action`` и ``continue_item_crafting_action``.
Порядок проверок и тексты ошибок сохранены 1:1.
"""
import logging
import uuid
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.characters import CharacterMiningStats

from ....resources.services.character_resource import CharacterResourceServiceProtocol
from ...exceptions import (
    CharacterNotInBuildingLocationError,
    CityTradingShopLicenseExpiredError,
    CityTradingShopNotFoundError,
    InsufficientCharacterLevelError,
    InsufficientCharacterTirednessError,
    InsufficientResourcesForCraftingError,
    NoCraftingLicenseError,
)
from ...repositories.building.building import BuildingRepositoryProtocol
from ...repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ...schemas import BuildingReadSchema, ItemReadSchema
from ...services.crafting_license.crafting_license import CraftingLicenseServiceProtocol
from ...services.items.items_component import ItemComponentServiceProtocol

logger = logging.getLogger(__name__)

PRODUCTION_LOCATION_SLUGS = {"1.13.forge", "1.16.jewelers"}


class CraftingValidatorProtocol(Protocol):
    """Контракт валидатора запуска крафта."""

    async def validate(
        self, character: CharacterMiningStats, item: ItemReadSchema
    ) -> BuildingReadSchema:
        ...

    async def validate_character(self, character: CharacterMiningStats) -> None:
        ...

    async def validate_location_and_license(
        self, character: CharacterMiningStats, item: ItemReadSchema
    ) -> BuildingReadSchema:
        ...

    async def validate_resources(self, character_id: uuid.UUID, item_slug: str) -> None:
        ...


class CraftingValidator(CraftingValidatorProtocol):
    """Проверки допуска персонажа к крафту: уровень, усталость, локация/лицензия, ресурсы."""

    def __init__(
        self,
        building_repository: BuildingRepositoryProtocol,
        city_trading_shop_repository: CityTradingShopCharacterRepositoryProtocol,
        item_component_service: ItemComponentServiceProtocol,
        character_resource_service: CharacterResourceServiceProtocol,
        crafting_license_service: CraftingLicenseServiceProtocol | None = None,
        min_valid_level: int = 3,
        max_valid_tiredness: float = 0.495,
    ):
        self.building_repository = building_repository
        self.city_trading_shop_repository = city_trading_shop_repository
        self.item_component_service = item_component_service
        self.character_resource_service = character_resource_service
        self.crafting_license_service = crafting_license_service
        self.min_valid_level = min_valid_level
        self.max_valid_tiredness = max_valid_tiredness

    async def validate(
        self, character: CharacterMiningStats, item: ItemReadSchema
    ) -> BuildingReadSchema:
        """Полная проверка допуска к крафту.

        Кидает соответствующее исключение при провале проверки, иначе
        возвращает здание крафта (чтобы вызывающий код не делал повторный SELECT).
        """
        await self.validate_character(character)
        building = await self.validate_location_and_license(character, item)
        await self.validate_resources(character.id, item.slug)
        return building

    async def validate_character(self, character: CharacterMiningStats) -> None:
        """Проверка уровня и усталости персонажа."""
        if character.level < self.min_valid_level:
            logger.warning(
                "Character %s does not meet level requirement: %s < %s",
                character.id, character.level, self.min_valid_level
            )
            raise InsufficientCharacterLevelError(
                required_level=self.min_valid_level, current_level=character.level
            )

        if character.tiredness >= self.max_valid_tiredness:
            logger.warning(
                "Character %s tiredness too high: %s > %s",
                character.id, character.tiredness, self.max_valid_tiredness
            )
            raise InsufficientCharacterTirednessError(
                required_tiredness=self.max_valid_tiredness,
                current_tiredness=character.tiredness
            )


    async def validate_location_and_license(
        self, character: CharacterMiningStats, item: ItemReadSchema
    ) -> BuildingReadSchema:
        """Проверка локации здания и лицензии (мастера либо городской лавки)."""
        building = await self.building_repository.get_by_city_trading_location(item.location_slug)
        if building.location_slug != character.location_slug:
            logger.warning(
                "Character %s not in building location: required=%s current=%s",
                character.id, building.location_slug, character.location_slug
            )
            raise CharacterNotInBuildingLocationError(
                required_location=building.location_slug,
                current_location=character.location_slug
            )

        if item.location_slug not in PRODUCTION_LOCATION_SLUGS:
            city_shop = await self.city_trading_shop_repository.get_by_location_and_character(
                location_slug=building.city_trading_location_slug,
                character_id=character.id
            )
            if not city_shop:
                raise CityTradingShopNotFoundError(
                    location_slug=building.city_trading_location_slug,
                    character_id=character.id
                )
            now = datetime.now(UTC)
            if not city_shop.end_license or city_shop.end_license <= now:
                raise CityTradingShopLicenseExpiredError(
                    location_slug=building.city_trading_location_slug,
                    end_license=str(city_shop.end_license) if city_shop.end_license else None
                )
        else:
            # Для кузницы/ювелирной проверяем лицензию мастера
            if self.crafting_license_service is None:
                raise RuntimeError("Crafting license service is not available")
            license_status = await self.crafting_license_service.get_status(
                character.id, item.location_slug
            )
            if not license_status.is_active:
                raise NoCraftingLicenseError(item.location_slug)

        return building

    async def validate_resources(self, character_id: uuid.UUID, item_slug: str) -> None:
        """Проверка наличия ресурсов для крафта предмета."""
        components = await self.item_component_service.get_components_with_resource_names(item_slug)
        missing_resources = {}
        for component in components:
            character_resource = await self.character_resource_service.get_by_character_and_resource(
                character_id, component.resource_slug
            )
            if not character_resource or character_resource.amount < component.quantity:
                current_amount = character_resource.amount if character_resource else 0
                missing_resources[component.resource_name] = {
                    "required": component.quantity,
                    "current": current_amount
                }

        if missing_resources:
            logger.warning(
                "Character %s has insufficient resources for item %s: %s",
                character_id, item_slug, missing_resources
            )
            raise InsufficientResourcesForCraftingError(missing_resources=missing_resources)
