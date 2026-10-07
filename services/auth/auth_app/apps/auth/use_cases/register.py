from fastapi import Request
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..schemas import UserAndCharacterCreateSchema, PlayAuthSchema
from ..services.auth import AuthServiceProtocol 


class RegisterUseCaseProtocol(UseCaseProtocol[PlayAuthSchema]):
    async def __call__(self: Self, request: Request, data: UserAndCharacterCreateSchema) -> PlayAuthSchema:
        ...


class RegisterUseCase(RegisterUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, data: UserAndCharacterCreateSchema) -> PlayAuthSchema:
        ip_addr = request.client.host
        return await self.service.register(ip_addr, data)
