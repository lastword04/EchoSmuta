from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.users import (
    UserCreateSchema,
    UserReadSchema,
    UserLoginSchema,
    PasswordSchema
)
from ....core.adapters.base_http import BaseHttpClientImpl

class UserServiceClientProtocol(Protocol):
    async def register(self: Self, user: UserCreateSchema) -> UserReadSchema:
        """Регистрация нового пользователя"""
        ...

    async def delete(self: Self, user_id: str) -> None:
        """Удаление пользователя по ID"""
        ...

    async def login(self: Self, user: UserLoginSchema) -> UserReadSchema:
        """Авторизация пользователя"""
        ...

    async def get(self: Self, user_id: str) -> UserReadSchema:
        """Получение пользователя по ID"""
        ...

    async def get_by_email(self: Self, email: str) -> UserReadSchema:
        """Получение пользователя по email"""
        ...

    async def change_password(self: Self, user_id: str, password: PasswordSchema) -> UserReadSchema:
        """Изменение пароля пользователя"""
        ...

class UserServiceClient(BaseHttpClientImpl, UserServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] = ["users:read", "users:write"] 
    ):
        super().__init__(
            base_url=base_url,
            target_service="user-service", 
            permissions=permissions,
            timeout=timeout
        )

    async def register(self: Self, user: UserCreateSchema) -> UserReadSchema:
        """Создание нового пользователя"""
        return await self.request(
            "POST",
            "/register",
            response_model=UserReadSchema,
            error_model=BaseResponseSchema,
            json=user.model_dump(mode='json'),
        )
    
    async def delete(self: Self, user_id: str) -> None:
        """Удаление пользователя по ID"""
        await self.request(
            "DELETE",
            f"/{user_id}",
            response_model=None,
            error_model=BaseResponseSchema,
        )
        return None
    
    async def login(self: Self, user: UserLoginSchema) -> UserReadSchema:
        """Авторизация пользователя"""
        return await self.request(
            "POST",
            "/login",
            response_model=UserReadSchema,
            error_model=BaseResponseSchema,
            json=user.model_dump(mode='json'),
        )

    async def get(self: Self, user_id: str) -> UserReadSchema:
        """Получение пользователя по ID"""
        return await self.request(
            "GET",
            f"/{user_id}",
            response_model=UserReadSchema,
            error_model=BaseResponseSchema,
        )
    
    async def get_by_email(self: Self, email: str) -> UserReadSchema:
        """Получение пользователя по email"""
        return await self.request(
            "GET",
            f"/email/{email}",
            response_model=UserReadSchema,
            error_model=BaseResponseSchema,
        )
    
    async def change_password(self: Self, user_id: str, password: PasswordSchema) -> UserReadSchema:
        """Изменение пароля пользователя"""
        return await self.request(
            "PUT",
            f"/{user_id}/change-password",
            response_model=UserReadSchema,
            error_model=BaseResponseSchema,
            json=password.model_dump(mode='json'),
        )