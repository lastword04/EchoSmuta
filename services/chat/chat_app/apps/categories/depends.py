from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from ...settings import Settings, get_settings
from ..messages.use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol
from ..messages.depends_shared import get_valid_status_character_use_case
from .adapter.characters import CharacterServiceClientProtocol, CharacterServiceClient
from .repositories.categories import CategoryRepositoryProtocol, CategoryRepository
from .repositories.categories_characters import CategoryCharacterRepositoryProtocol, CategoryCharacterRepository
from .services.categories import CategoryServiceProtocol, CategoryService
from .services.categories_characters import CategoryCharacterServiceProtocol, CategoryCharacterService
from .use_cases.categories.create_default import CreateDefaultCategoriesUseCaseProtocol, CreateDefaultCategoriesUseCase
from .use_cases.categories.create import CreateCategoriesUseCaseProtocol, CreateCategoriesUseCase
from .use_cases.categories.delete import DeleteCategoriesUseCaseProtocol, DeleteCategoriesUseCase
from .use_cases.categories.get_my import GetMyCategoriesUseCaseProtocol, GetMyCategoriesUseCase
from .use_cases.categories.get_my_with_counts import GetMyWithCountsCategoriesUseCaseProtocol, GetMyWithCountsCategoriesUseCase
from .use_cases.categories.update_checkbox import UpdateCategoriesUseCaseProtocol, UpdateCategoriesUseCase
from .use_cases.categories_characters.add_character_to_category import AddCharacterToCategoryUseCaseProtocol, AddCharacterToCategoryUseCase
from .use_cases.categories_characters.get_by_category import GetByCategoryUseCaseProtocol, GetByCategoryUseCase
from .use_cases.categories_characters.delete_character_from_category import DeleteCharacterFromCategoryUseCaseProtocol, DeleteCharacterFromCategoryUseCase
from .use_cases.categories.calculate_stats_base_category import GetCategoriesStatsUseCaseProtocol, GetCategoriesStatsUseCase 

# categories
def __get_categories_repository(session: AsyncSession = Depends(get_async_session)) -> CategoryRepositoryProtocol:
    return CategoryRepository(session)

def get_categories_service(repository: CategoryRepositoryProtocol = Depends(__get_categories_repository),
                           settings: Settings = Depends(get_settings)) -> CategoryServiceProtocol:
    return CategoryService(repository, settings.category.limit,
                           settings.category.main_max_count_characters,
                           settings.category.not_main_max_count_characters)

def get_categories_create_default_use_case(service: CategoryServiceProtocol = Depends(get_categories_service)) -> CreateDefaultCategoriesUseCaseProtocol:
    return CreateDefaultCategoriesUseCase(service)

def get_create_category_use_case(service: CategoryServiceProtocol = Depends(get_categories_service),
                                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> CreateCategoriesUseCaseProtocol:
    return CreateCategoriesUseCase(service, valid_or_raise)

def get_delete_category_use_case(service: CategoryServiceProtocol = Depends(get_categories_service),
                                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> DeleteCategoriesUseCaseProtocol:
    return DeleteCategoriesUseCase(service, valid_or_raise)

def get_get_my_categories_use_case(service: CategoryServiceProtocol = Depends(get_categories_service),
                                   valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> GetMyCategoriesUseCaseProtocol:
    return GetMyCategoriesUseCase(service, valid_or_raise)

def get_get_my_with_counts_categories_use_case(service: CategoryServiceProtocol = Depends(get_categories_service),
                                               valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> GetMyWithCountsCategoriesUseCaseProtocol:
    return GetMyWithCountsCategoriesUseCase(service, valid_or_raise)

def get_update_checkbox_for_categories_use_case(service: CategoryServiceProtocol = Depends(get_categories_service),
                                               valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)
                                               ) -> UpdateCategoriesUseCaseProtocol:
    return UpdateCategoriesUseCase(service, valid_or_raise)

def get_categories_stats_use_case(service: CategoryServiceProtocol = Depends(get_categories_service)) -> GetCategoriesStatsUseCaseProtocol:
    return GetCategoriesStatsUseCase(service)                                                

# categories characters
def __get_category_character_repository(session: AsyncSession = Depends(get_async_session)) -> CategoryCharacterRepositoryProtocol:
    return CategoryCharacterRepository(session)

def get_character_adapter(settings: Settings = Depends(get_settings)) -> CharacterServiceClientProtocol:
    return CharacterServiceClient(base_url=settings.character_service_app.base_url)

def get_category_character_service(repository: CategoryCharacterRepositoryProtocol = Depends(__get_category_character_repository),
                                   character_service: CharacterServiceClientProtocol = Depends(get_character_adapter)
                                   ) -> CategoryCharacterServiceProtocol:
    return CategoryCharacterService(repository, character_service)
    
def get_add_character_to_category(service: CategoryCharacterServiceProtocol = Depends(get_category_character_service),
                                  valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> AddCharacterToCategoryUseCaseProtocol:
    return AddCharacterToCategoryUseCase(service, valid_or_raise)

def get_get_by_category(service: CategoryCharacterServiceProtocol = Depends(get_category_character_service),
                        valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> GetByCategoryUseCaseProtocol:
    return GetByCategoryUseCase(service, valid_or_raise)

def get_delete_character_from_category_use_case(service: CategoryCharacterServiceProtocol = Depends(get_category_character_service),
                                                valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_valid_status_character_use_case)) -> DeleteCharacterFromCategoryUseCaseProtocol:
    return DeleteCharacterFromCategoryUseCase(service, valid_or_raise)