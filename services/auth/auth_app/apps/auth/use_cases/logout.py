from fastapi import Request
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol 
from ..services.auth import AuthServiceProtocol
from ..schemas import SessionUserEventRequestSchema


class LogoutUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, user: UserTokenDataReadSchema, token: str) -> None:
        ...


class LogoutUseCase(LogoutUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, user: UserTokenDataReadSchema, token: str) -> None:
        ip_addr = request.client.host
        await self.service.logout(ip_addr, user.user_id, session_request, token)
