from shared.schemas.users import UserReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.users import UserServiceProtocol


class GetByEmailUseCaseProtocol(UseCaseProtocol[UserReadSchema]):
    async def __call__(self, email: str) -> UserReadSchema: ...


class GetByEmailUseCase(GetByEmailUseCaseProtocol):
    def __init__(self, user_service: UserServiceProtocol):
        self.user_service = user_service

    async def __call__(self, email: str) -> UserReadSchema:
        return await self.user_service.get_by_email(email)
