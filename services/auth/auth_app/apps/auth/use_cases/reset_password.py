from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..schemas import UserResetSchema
from ..services.reset_passwords import ResetPasswordServiceProtocol 


class ResetPasswordUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self, data: UserResetSchema) -> bool:
        ...


class ResetPasswordUseCase(ResetPasswordUseCaseProtocol):
    def __init__(self: Self, service: ResetPasswordServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: UserResetSchema) -> bool:
        return await self.service.reset_password(data)
