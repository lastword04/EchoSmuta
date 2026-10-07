import uuid
from shared.schemas.category import BaseCategoryStatsSchema 
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol

class GetCategoriesStatsUseCaseProtocol(UseCaseProtocol[BaseCategoryStatsSchema]):
    async def __call__(self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        ...

class GetCategoriesStatsUseCase(GetCategoriesStatsUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        return await self.service.calculate_stats_base_category(character_id)