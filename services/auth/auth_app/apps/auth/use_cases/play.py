from fastapi import Request
import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol 
from ..schemas import PlayAuthSchema, SessionUserEventRequestSchema
from ..services.auth import AuthServiceProtocol 


class PlayUseCaseProtocol(UseCaseProtocol[PlayAuthSchema]):
    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        ...


class PlayUseCase(PlayUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        ip_address = request.client.host
        return await self.service.play(ip_address, session_request, character_id, user, refresh_token)
