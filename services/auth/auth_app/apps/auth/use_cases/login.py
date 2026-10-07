from fastapi import Request
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..schemas import LoginSchema, AuthSchema
from ..services.auth import AuthServiceProtocol


class LoginUseCaseProtocol(UseCaseProtocol[AuthSchema]):
    async def __call__(self: Self, request: Request, data: LoginSchema) -> AuthSchema:
        ...


class LoginUseCase(LoginUseCaseProtocol):
    def __init__(self: Self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self: Self, request: Request, data: LoginSchema) -> AuthSchema:
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        fingerprint = data.fingerprint if hasattr(data, "fingerprint") else None
        return await self.service.login(
            ip_address=ip_address,
            credentials=data,
            user_agent=user_agent,
            fingerprint=fingerprint,
        )