import uuid
from .....core.use_cases import UseCaseProtocol
from ...services.categories import CategoryServiceProtocol
from ...schemas import CategoryReadSchema

class CreateDefaultCategoriesUseCaseProtocol(UseCaseProtocol[list[CategoryReadSchema]]):
    async def __call__(self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        ...

class CreateDefaultCategoriesUseCase(CreateDefaultCategoriesUseCaseProtocol):
    def __init__(self, service: CategoryServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        return await self.service.create_default(character_id)