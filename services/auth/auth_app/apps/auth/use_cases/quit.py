from fastapi import Request
import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol 
from ..services.auth import AuthServiceProtocol
from ..schemas import AuthTokensSchema, SessionUserEventRequestSchema


class QuitUseCaseProtocol(UseCaseProtocol[AuthTokensSchema]):
    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> AuthTokensSchema:
        ...


class QuitUseCase(QuitUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, session_request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> AuthTokensSchema:
        ip_address = request.client.host
        return await self.service.quit(ip_address, session_request, character_id, user, refresh_token)
