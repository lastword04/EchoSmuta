from fastapi import Request
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol 
from ..schemas import PlayAuthSchema, SessionUserEventRequestSchema
from ..services.auth import AuthServiceProtocol 


class PlayMainUseCaseProtocol(UseCaseProtocol[PlayAuthSchema]):
    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        ...


class PlayMainUseCase(PlayMainUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        ip_address = request.client.host
        return await self.service.play_main(ip_address, session_request, user, refresh_token)
