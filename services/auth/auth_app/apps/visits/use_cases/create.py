from fastapi import Request
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..schemas import NewUsersVisitRequestSchema, NewUsersVisitReadSchema
from ..services.visits import NewUsersVisitServiceProtocol 


class NewUsersVisitUseCaseProtocol(UseCaseProtocol[NewUsersVisitReadSchema]):
    async def __call__(self: Self, request: Request, data: NewUsersVisitRequestSchema) -> NewUsersVisitReadSchema:
        ...


class NewUsersVisitUseCase(NewUsersVisitUseCaseProtocol):
    def __init__(self: Self, service: NewUsersVisitServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, data: NewUsersVisitRequestSchema) -> NewUsersVisitReadSchema:
        ip_addr = request.client.host
        return await self.service.create(ip_addr, data)
