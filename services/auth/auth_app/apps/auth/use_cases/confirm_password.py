from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..schemas import ResetPasswordRequest
from ..services.reset_passwords import ResetPasswordServiceProtocol 


class ConfirmPasswordUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self, data: ResetPasswordRequest) -> bool:
        ...


class ConfirmPasswordUseCase(ConfirmPasswordUseCaseProtocol):
    def __init__(self: Self, service: ResetPasswordServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: ResetPasswordRequest) -> bool:
        return await self.service.confirm_reset_password(data)
