from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..characters.services.character.characters import (
    GetMainCharacterByUserIdProtocol,
    UpdateCharacterProtocol
)
from ...apps.characters.deps import (
    get_main_character_by_user_id_service,
    get_update_character_service
)
from ...core.db import get_async_session
from .repositories.exchanges import ExchangeSettingsRepositoryProtocol, ExchangeSettingsRepository
from .repositories.slots import SlotRepositoryProtocol, SlotRepository
from .adapters.characters import (
    GetMainCharacterAdapterProtocol, GetMainCharacterAdapter,
    UpdateCharacterAdapterProtocol, UpdateCharacterAdapter
)
from .services.exchanges import ExchangeSettingsServiceProtocol, ExchangeSettingsService
from .services.slots import (
    CreateSlotServiceProtocol, CreateSlotService,
    DeleteSlotServiceProtocol, DeleteSlotService,
    GetSlotsServiceProtocol, GetSlotsService,
    BuySlotServiceProtocol, BuySlotService
)
from .use_cases.initializators.init_exchanges_settings import (
    InitializeExchangeSettingsUseCaseProtocol,
    InitializeExchangeSettingsUseCase
)
from .use_cases.exchanges_settings.get import (
    GetExchangeSettingsUseCaseProtocol,
    GetExchangeSettingsUseCase
)
from .use_cases.slots.create import (
    CreateSlotUseCaseProtocol,
    CreateSlotUseCase
)
from .use_cases.slots.delete import (
    DeleteSlotUseCaseProtocol,
    DeleteSlotUseCase
)
from .use_cases.slots.paginate import (
    GetPaginatedSlotsUseCaseProtocol,
    GetPaginatedSlotsUseCase
)
from .use_cases.slots.buy import (
    BuySlotUseCaseProtocol,
    BuySlotUseCase
)

def __get_exchange_settings_repository(
    session: AsyncSession = Depends(get_async_session)
) -> ExchangeSettingsRepositoryProtocol:
    return ExchangeSettingsRepository(session=session)


def get_exchange_settings_service(
    repository: ExchangeSettingsRepositoryProtocol = Depends(__get_exchange_settings_repository)
) -> ExchangeSettingsServiceProtocol:
    return ExchangeSettingsService(repository=repository)


def get_initialize_exchange_settings_use_case(
    session: AsyncSession
) -> InitializeExchangeSettingsUseCaseProtocol:
    repo = __get_exchange_settings_repository(session=session)
    service = get_exchange_settings_service(repository=repo)
    return InitializeExchangeSettingsUseCase(service=service)

def get_get_all_exchange_settings_use_case(
    service: ExchangeSettingsServiceProtocol = Depends(get_exchange_settings_service)
) -> GetExchangeSettingsUseCaseProtocol:
    return GetExchangeSettingsUseCase(service=service)

def __get_slot_repository(
    session: AsyncSession = Depends(get_async_session)
) -> SlotRepositoryProtocol:
    return SlotRepository(session=session)

def get_character_service_adapter(
    service: GetMainCharacterByUserIdProtocol = Depends(get_main_character_by_user_id_service)
) -> GetMainCharacterAdapterProtocol:
    return GetMainCharacterAdapter(service=service)

def get_character_update_adapter(
    service: UpdateCharacterProtocol = Depends(get_update_character_service)
) -> UpdateCharacterAdapterProtocol:
    return UpdateCharacterAdapter(service=service)

def get_create_slot_service(
    repository: SlotRepositoryProtocol = Depends(__get_slot_repository),
    exchange_settings: ExchangeSettingsServiceProtocol = Depends(get_exchange_settings_service),
    character_service: GetMainCharacterAdapterProtocol = Depends(get_character_service_adapter),
    character_update_service: UpdateCharacterAdapterProtocol = Depends(get_character_update_adapter)
) -> CreateSlotServiceProtocol:
    return CreateSlotService(repository=repository, 
                             exchange_settings=exchange_settings, 
                             character_service=character_service, 
                             character_update_service=character_update_service)

def get_create_slot_use_case(
    slot_service: CreateSlotServiceProtocol = Depends(get_create_slot_service)
) -> CreateSlotUseCaseProtocol:
    return CreateSlotUseCase(service=slot_service)

def get_delete_slot_service(
    repository: SlotRepositoryProtocol = Depends(__get_slot_repository),
    character_service: GetMainCharacterAdapterProtocol = Depends(get_character_service_adapter),
    character_update_service: UpdateCharacterAdapterProtocol = Depends(get_character_update_adapter),
    exchange_settings: ExchangeSettingsServiceProtocol = Depends(get_exchange_settings_service)
) -> DeleteSlotServiceProtocol:
    return DeleteSlotService(repository=repository, 
                             character_service=character_service, 
                             character_update_service=character_update_service,
                             exchange_settings=exchange_settings)

def get_delete_slot_use_case(
    slot_service: DeleteSlotServiceProtocol = Depends(get_delete_slot_service)
) -> DeleteSlotUseCaseProtocol:
    return DeleteSlotUseCase(service=slot_service)

def get_get_slots_service(
    repository: SlotRepositoryProtocol = Depends(__get_slot_repository),
    character_service: GetMainCharacterAdapterProtocol = Depends(get_character_service_adapter),
) -> GetSlotsServiceProtocol:
    return GetSlotsService(repository=repository, character_service=character_service)

def get_get_paginated_slots_use_case(
    slot_service: GetSlotsServiceProtocol = Depends(get_get_slots_service)
) -> GetPaginatedSlotsUseCaseProtocol:
    return GetPaginatedSlotsUseCase(service=slot_service)

def get_buy_slot_service(
    repository: SlotRepositoryProtocol = Depends(__get_slot_repository),
    character_service: GetMainCharacterAdapterProtocol = Depends(get_character_service_adapter),
    character_update_service: UpdateCharacterAdapterProtocol = Depends(get_character_update_adapter),
) -> BuySlotServiceProtocol:
    return BuySlotService(repository=repository, 
                          character_service=character_service, 
                          character_update_service=character_update_service)

def get_buy_slot_use_case(
    slot_service: BuySlotServiceProtocol = Depends(get_buy_slot_service)
) -> BuySlotUseCaseProtocol:
    return BuySlotUseCase(service=slot_service)