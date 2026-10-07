"""Провайдеры items-домена: каталог предметов, цены, компоненты, экипировка.

get_character_item_service импортируется из .character (инвентарь персонажа
нужен для equip/unpack_kit/use_consumable), поэтому character.py от items.py
не зависит и цикла нет.
"""
from fastapi import Depends

from ..adapters.characters import CharacterServiceClientProtocol
from ..events.items import ItemEventsProtocol
from ..repositories.character.character_equipment import (
    CharacterEquipmentRepositoryProtocol,
)
from ..repositories.character.character_items import CharacterItemRepositoryProtocol
from ..repositories.items.experience_for_level import (
    ItemExperienceForLevelRepositoryProtocol,
)
from ..repositories.items.items import ItemRepositoryProtocol
from ..repositories.items.items_component import ItemComponentRepositoryProtocol
from ..repositories.items.items_price import ItemPriceRepositoryProtocol
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from ..services.character.character_items import CharacterItemServiceProtocol
from ..services.character.equipment import EquipmentService, EquipmentServiceProtocol
from ..services.items.experience_for_level import (
    ItemExperienceForLevelService,
    ItemExperienceForLevelServiceProtocol,
)
from ..services.items.items import ItemService, ItemServiceProtocol
from ..services.items.items_component import (
    ItemComponentService,
    ItemComponentServiceProtocol,
)
from ..services.items.items_price import ItemPriceService, ItemPriceServiceProtocol
from ..use_cases.items.equip import EquipItemUseCase, EquipItemUseCaseProtocol
from ..use_cases.items.get_item_by_slug import (
    GetItemBySlugUseCase,
    GetItemBySlugUseCaseProtocol,
)
from ..use_cases.items.get_item_details import (
    GetItemDetailsUseCase,
    GetItemDetailsUseCaseProtocol,
)
from ..use_cases.items.get_my_equipment import (
    GetMyEquipmentUseCase,
    GetMyEquipmentUseCaseProtocol,
)
from ..use_cases.items.repair import RepairItemUseCase, RepairItemUseCaseProtocol
from ..use_cases.items.unequip import UnequipItemUseCase, UnequipItemUseCaseProtocol
from ..use_cases.items.unpack_kit import UnpackKitUseCase, UnpackKitUseCaseProtocol
from ..use_cases.items.use_consumable import (
    UseConsumableUseCase,
    UseConsumableUseCaseProtocol,
)
from .adapters import get_character_service_client, get_item_template_service
from .character import get_character_item_service
from .events import get_items_events
from .repositories import (
    _get_character_equipment_repository,
    _get_character_item_repository,
    _get_item_component_repository,
    _get_item_experience_for_level_repository,
    _get_item_price_repository,
    _get_item_repository,
)


# item service and use cases
def get_item_service(repository: ItemRepositoryProtocol = Depends(_get_item_repository), component_repository: ItemComponentRepositoryProtocol = Depends(_get_item_component_repository)) -> ItemServiceProtocol:
    return ItemService(repository=repository, component_repository=component_repository)


# item price
def get_item_price_service(repository: ItemPriceRepositoryProtocol = Depends(_get_item_price_repository)) -> ItemPriceServiceProtocol:
    return ItemPriceService(repository=repository)


# item component service and use cases
def get_item_component_service(repository: ItemRepositoryProtocol = Depends(_get_item_component_repository)) -> ItemComponentServiceProtocol:
    return ItemComponentService(repository=repository)


def get_equipment_service(
    equipment_repository: CharacterEquipmentRepositoryProtocol = Depends(_get_character_equipment_repository),
    character_item_repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client),
    item_component_service: ItemComponentServiceProtocol = Depends(get_item_component_service),
) -> EquipmentServiceProtocol:
    return EquipmentService(
        equipment_repository=equipment_repository,
        character_item_repository=character_item_repository,
        character_service=character_service,
        item_component_service=item_component_service,
    )

def get_equip_item_use_case(
    service: EquipmentServiceProtocol = Depends(get_equipment_service),
    inventory_service: CharacterItemServiceProtocol = Depends(get_character_item_service),
    characters_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
) -> EquipItemUseCaseProtocol:
    return EquipItemUseCase(
        service=service,
        inventory_service=inventory_service,
        characters_client=characters_client,
    )

def get_unequip_item_use_case(service: EquipmentServiceProtocol = Depends(get_equipment_service)) -> UnequipItemUseCaseProtocol:
    return UnequipItemUseCase(service)

def get_unpack_kit_use_case(
    inventory_service: CharacterItemServiceProtocol = Depends(get_character_item_service),
) -> UnpackKitUseCaseProtocol:
    return UnpackKitUseCase(inventory_service=inventory_service)

def get_get_my_equipment_use_case(
    equipment_service: EquipmentServiceProtocol = Depends(get_equipment_service)
) -> GetMyEquipmentUseCaseProtocol:
    return GetMyEquipmentUseCase(equipment_service=equipment_service)

def get_repair_item_use_case(service: EquipmentServiceProtocol = Depends(get_equipment_service)) -> RepairItemUseCaseProtocol:
    return RepairItemUseCase(service)


# items
def get_get_item_by_slug_use_case(
    service: ItemServiceProtocol = Depends(get_item_service)
) -> GetItemBySlugUseCaseProtocol:
    return GetItemBySlugUseCase(service=service)

def get_get_item_details_use_case(
    service: ItemServiceProtocol = Depends(get_item_service)
) -> GetItemDetailsUseCaseProtocol:
    return GetItemDetailsUseCase(service=service)

def get_use_consumable_use_case(
    inventory_service: CharacterItemServiceProtocol = Depends(get_character_item_service),
    characters_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
) -> UseConsumableUseCaseProtocol:
    return UseConsumableUseCase(
        inventory_service=inventory_service,
        characters_client=characters_client,
        items_events=items_events,
        template_service=template_service,
    )


# experience for level
def get_item_experience_for_level_service(repository: ItemExperienceForLevelRepositoryProtocol = Depends(_get_item_experience_for_level_repository)) -> ItemExperienceForLevelServiceProtocol:
    return ItemExperienceForLevelService(repository=repository)



def get_character_item_repository(
    repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
) -> CharacterItemRepositoryProtocol:
    return repository
