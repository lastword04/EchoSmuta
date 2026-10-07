from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_async_session
from ..characters.deps import get_get_online_status_or_raise_use_case
from ..characters.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol
from .repositories.panels import CharacterFastItemRepositoryProtocol, CharacterFastItemRepository
from .services.panels import ItemsCRUServiceProtocol, ItemsCRUService
from .use_cases.update import UpdateItemsUseCaseProtocol, UpdateItemsUseCase
from .use_cases.get_my import GetMyItemsUseCaseProtocol, GetMyItemsUseCase


def __get_items_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterFastItemRepositoryProtocol:
    return CharacterFastItemRepository(session)

def get_item_service(repository: CharacterFastItemRepositoryProtocol = Depends(__get_items_repository)) -> ItemsCRUServiceProtocol:
    return ItemsCRUService(repository)

def get_item_update_use_case(items_service: ItemsCRUServiceProtocol = Depends(get_item_service),
                             valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_get_online_status_or_raise_use_case)) -> UpdateItemsUseCaseProtocol:
    return UpdateItemsUseCase(items_service, valid_or_raise)

def get_item_get_my_use_case(items_service: ItemsCRUServiceProtocol = Depends(get_item_service),
                             valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_get_online_status_or_raise_use_case)) -> GetMyItemsUseCaseProtocol:
    return GetMyItemsUseCase(items_service, valid_or_raise)