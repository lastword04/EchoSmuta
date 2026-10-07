import uuid
import asyncio
from typing import Protocol, Optional
from typing_extensions import Self
from enum import Enum
from dataclasses import dataclass
import logging
from shared.schemas.base import StatusOkSchema
from shared.schemas.auth import UserTokenDataReadSchema
from shared.enums import UserRole
from shared.schemas.users import UserLoginSchema
from shared.schemas.captcha import CaptchaVerificationRequest
from ....core.utils.exceptions import ExternalServiceError, PermissionDeniedError
from ...visits.services.sessions import SessionUsersEventServiceProtocol
from ...visits.services.visits import NewUsersVisitServiceProtocol
from ...visits.enums import EventType
from ...visits.schemas import SessionUserEventRequestSchema
from ..schemas import (
    UserAndCharacterCreateSchema, UserAndCharacterReadSchema, LoginSchema,
    AuthSchema, PlayAuthSchema, TokenReadSchema, AuthTokensSchema
)
from ..adapters.users import UserServiceClientProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..adapters.captcha import CaptchaServiceClientProtocol
from ..events.characters import CharacterEventsProtocol
from .tokens import TokenServiceProtocol
from ..use_cases.log_auth_attempt import LogAuthAttemptUseCaseProtocol

logger = logging.getLogger(__name__)

class SagaStepStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class RegistrationSaga:
    user_id: Optional[uuid.UUID] = None
    character_id: Optional[uuid.UUID] = None
    user_step_status: SagaStepStatus = SagaStepStatus.PENDING
    character_step_status: SagaStepStatus = SagaStepStatus.PENDING

class AuthServiceProtocol(Protocol):
    async def register(
        self: Self, 
        ip_address: str,
        user_and_character: UserAndCharacterCreateSchema
    ) -> PlayAuthSchema:
        ...
    """Регистрация пользователя и персонажа"""
    async def login(self: Self, ip_address: str, credentials: LoginSchema) -> AuthSchema:
        ...

    async def refresh_token(self: Self, refresh_token: str) -> AuthSchema:
        """Обновление токена доступа по refresh token"""
        ...

    async def login_to_forum(self: Self, credentials: LoginSchema) -> AuthSchema:
        """Вход в форум с использованием учетных данных пользователя"""
        ...

    async def play(self: Self, ip_address: str, request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        """Вход в игру"""
        ...

    async def play_main(self: Self, ip_address: str, request: SessionUserEventRequestSchema, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        """Вход в игру за главного персонажа"""
        ...

    async def quit(self: Self, ip_address: str, request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> AuthTokensSchema:
        """Выход из игры"""
        ...

    async def logout(self: Self, ip_address: str, user_id: uuid.UUID, request: SessionUserEventRequestSchema, refresh_token: str) -> StatusOkSchema:
        """Выход с сайта (личного кабинета)"""
        ...

class AuthService(AuthServiceProtocol):
    def __init__(
        self,
        user_client: UserServiceClientProtocol,
        character_client: CharacterServiceClientProtocol,
        captcha_client: CaptchaServiceClientProtocol,
        token_service: TokenServiceProtocol,
        character_event: CharacterEventsProtocol,
        visit_service: NewUsersVisitServiceProtocol,
        session_service: SessionUsersEventServiceProtocol,
        log_auth_use_case: LogAuthAttemptUseCaseProtocol,
    ):
        self.user_client = user_client
        self.character_client = character_client
        self.token_service = token_service
        self.captcha_client = captcha_client
        self.character_event = character_event
        self.visit_service = visit_service
        self.session_service = session_service
        self.log_auth_use_case = log_auth_use_case

    async def login(self: Self, ip_address: str, credentials: LoginSchema, user_agent: Optional[str] = None, fingerprint: Optional[str] = None) -> AuthSchema:
        character_name = credentials.name
        user_id: Optional[uuid.UUID] = None
        character_id: Optional[uuid.UUID] = None

        try:
            try:
                character = await self.character_client.get_by_name(character_name)
                character_id = character.id
                user_id = character.user_id
                if not character.is_active:
                    logger.error(f"Character {character_name} is detached. Raise Permission Denied")
                    await self.log_auth_use_case(
                        ip_address=ip_address,
                        character_name=character_name,
                        success=False,
                        user_agent=user_agent,
                        fingerprint=fingerprint,
                        error_reason="character_detached",
                    )
                    raise PermissionDeniedError()

                if character.is_banned:
                    logger.error(f"Character {character_name} is banned. Raise Permission Denied")
                    await self.log_auth_use_case(
                        ip_address=ip_address,
                        character_name=character_name,
                        success=False,
                        user_agent=user_agent,
                        fingerprint=fingerprint,
                        error_reason="character_banned",
                    )
                    raise PermissionDeniedError()
            except ExternalServiceError as e:
                if e.status_code == 404:
                    logger.error(f"Not found character with name {character_name}. Raise Permission Denied")
                    await self.log_auth_use_case(
                        ip_address=ip_address,
                        character_name=character_name,
                        success=False,
                        user_agent=user_agent,
                        fingerprint=fingerprint,
                        error_reason="character_not_found",
                    )
                    raise PermissionDeniedError()
                raise

            user = await self.user_client.login(
                UserLoginSchema(
                    user_id=character.user_id,
                    password=credentials.password
                )
            )

            access_token, refresh_token = await self._create_tokens(user.id, user.role, character.is_main)

            await self.session_service.create(
                ip_address=ip_address,
                request=credentials.to_session_request_schema(),
                event_type=EventType.LOGIN,
                character_id=character.id
            )

            await self.log_auth_use_case(
                ip_address=ip_address,
                character_name=character_name,
                success=True,
                user_agent=user_agent,
                fingerprint=fingerprint,
                user_id=user.id,
                character_id=character.id,
            )

            return AuthSchema(
                user=user,
                character=character,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except PermissionDeniedError:
            raise
        except Exception as e:
            await self.log_auth_use_case(
                ip_address=ip_address,
                character_name=character_name,
                success=False,
                user_agent=user_agent,
                fingerprint=fingerprint,
                user_id=user_id,
                character_id=character_id,
                error_reason=f"{type(e).__name__}: {str(e)[:200]}",
            )
            raise

    async def login_to_forum(self: Self, credentials: LoginSchema) -> AuthSchema:
        try:
            character = await self.character_client.get_by_name(credentials.name)
            if not character.is_active:
                logger.error(f"Character {credentials.name} is detached. Raise Permission Denied")
                raise PermissionDeniedError()

            if character.is_banned:
                logger.error(f"Character {credentials.name} is banned. Raise Permission Denied")
                raise PermissionDeniedError()
        except ExternalServiceError as e:
            if e.status_code == 404:
                logger.error(f"Not found character with name {credentials.name}. Raise Permission Denied")
                raise PermissionDeniedError()
            raise

        if not character.is_main:
            logger.error(f"Character {character.id} is not main. Raise Permission Denied")
            raise PermissionDeniedError()
        logger.info(f"Logging in user {credentials.name} with character {character.id}")
        user = await self.user_client.login(
            UserLoginSchema(
                user_id=character.user_id,
                password=credentials.password   
            )
        )

        access_token, refresh_token = await self._create_tokens(user.id, user.role, character.is_main)

        return AuthSchema(
            user=user,
            character=character,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self: Self, refresh_token: str) -> AuthSchema:
        logger.info("Refreshing tokens")
        db_token = await self.token_service.verify_refresh_token(refresh_token)

        character = await self.character_client.get_simple(db_token.character_id) if db_token.character_id else None

        user = await self.user_client.get(db_token.user_id)
        
        await self.token_service.delete(db_token.id)

        character_id = character.id if character and character.is_online else None

        access_token, new_refresh_data = await self._create_tokens(user.id, user.role, db_token.is_main, character_id)
        logger.info(f"Tokens refreshed successfully for user: {user.id}")
        
        return AuthSchema(
            user=user,
            character=character,
            access_token=access_token,
            refresh_token=new_refresh_data,
        )
    
    async def logout(self: Self, ip_address: str, user_id: uuid.UUID, request: SessionUserEventRequestSchema, refresh_token: str) -> StatusOkSchema:
        _, characters = await asyncio.gather(
            self.token_service.delete_refresh_token(refresh_token),
            self.character_client.quit_all(user_id),
        )

        await self.session_service.bulk_create(
            ip_address=ip_address,
            request=request,
            event_type=EventType.LOGOUT,
            character_ids=characters.ids
        )
        
        await asyncio.gather(
            *[self.character_event.publish_character_quit(character_id) 
            for character_id in characters.ids]
        )


        return StatusOkSchema()

    async def play(self: Self, ip_address: str, request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        logger.info(f"Join to game with character {character_id}")

        character, _ = await asyncio.gather(
            self.character_client.play(character_id, user.user_id),
            self.token_service.delete_refresh_token(refresh_token)
        )
        
        access_token, new_refresh_data = await self._create_tokens(user.user_id, user.role, character.is_main, character_id)

        await self.character_event.publish_character_played(character)

        await self.session_service.create(
                ip_address=ip_address,
                request=request,
                event_type=EventType.PLAY,
                character_id=character.id
        )

        return PlayAuthSchema(
            character=character,
            access_token=access_token,
            refresh_token=new_refresh_data,
        )
    
    async def play_main(self: Self, ip_address: str, request: SessionUserEventRequestSchema, user: UserTokenDataReadSchema, refresh_token: str) -> PlayAuthSchema:
        logger.info(f"Join to game with main character for user {user.user_id}")

        character, _ = await asyncio.gather(
            self.character_client.play_main(user.user_id),
            self.token_service.delete_refresh_token(refresh_token)
        )

        access_token, new_refresh_data = await self._create_tokens(user.user_id, user.role, character.is_main, character.id)
        
        await self.session_service.create(
                ip_address=ip_address,
                request=request,
                event_type=EventType.PLAY,
                character_id=character.id
        )

        return PlayAuthSchema(
            character=character,
            access_token=access_token,
            refresh_token=new_refresh_data,
        )


    async def quit(self: Self, ip_address: str, request: SessionUserEventRequestSchema, character_id: uuid.UUID, user: UserTokenDataReadSchema, refresh_token: str) -> AuthTokensSchema:
        logger.info(f"Quit from game with character: {character_id}")
        await asyncio.gather(
            self.character_client.quit(character_id, user.user_id),
            self.token_service.delete_refresh_token(refresh_token)
        )
        
        access_token, new_refresh_data = await self._create_tokens(user.user_id, user.role)

        await self.session_service.create(
            ip_address=ip_address,
            request=request,
            event_type=EventType.QUIT,
            character_id=character_id
        )

        await self.character_event.publish_character_quit(character_id)

        return AuthTokensSchema(
            access_token=access_token, 
            refresh_token=new_refresh_data
        )
    
    async def _create_tokens(self: Self, user_id: uuid.UUID, role: UserRole, 
                             is_main: bool = False, character_id: Optional[uuid.UUID] = None) -> tuple[TokenReadSchema, TokenReadSchema]:
        access_token = self.token_service.create_access_token(
            user_id=user_id,
            character_id=character_id,
            role=role, 
            is_main=is_main
        )

        refresh_token = await self.token_service.create_refresh_token(user_id, is_main, character_id)

        logger.info(f"Access token created for character: {character_id}")
        logger.info(f"Tokens refreshed successfully for user: {user_id}")

        return access_token, refresh_token


    async def register(
        self: Self, 
        ip_address: str,
        user_and_character: UserAndCharacterCreateSchema
    ) -> PlayAuthSchema:
        saga = RegistrationSaga()
        logger.info("Starting registration saga")
        
        try:
            # Step 0: Verify captcha
            captcha_request = CaptchaVerificationRequest(
                captcha_id=user_and_character.captcha_id,
                user_input=user_and_character.user_input
            )
            logger.info(f"Verifying captcha with ID: {captcha_request.captcha_id[:8]}...")
            await self.captcha_client.verify_captcha(captcha_request)
            # Step 1: Create user
            logger.info("Step 1: Creating user")
            user_for_create = user_and_character.to_user_create_schema()
            user = await self.user_client.register(user_for_create)
            saga.user_id = user.id
            saga.user_step_status = SagaStepStatus.COMPLETED
            logger.info(f"User created successfully with ID: {user.id}")
            
            # Step 2: Create character
            logger.info("Step 2: Creating character")
            character_for_create = user_and_character.to_character_create_schema(user.id)
            character = await self.character_client.create(character_for_create)
            saga.character_id = character.id
            saga.character_step_status = SagaStepStatus.COMPLETED
            logger.info(f"Character created successfully with ID: {character.id}")

            play_character = await self.character_client.play(character.id, user.id)

            # await self.visit_service.register(ip_address, user_and_character.fingerprint, user_and_character.referral_code, user_and_character.visit_id, character.id)
            # await self.session_service.create(
            #     ip_address=ip_address,
            #     request=user_and_character.to_session_request_schema(),
            #     event_type=EventType.REGISTER,
            #     character_id=character.id
            # )

            access_token, new_refresh_data = await self._create_tokens(user.id, user.role, play_character.is_main, play_character.id)

            logger.info("Registration saga completed successfully")
            
            return PlayAuthSchema(
                character=character,
                access_token=access_token,
                refresh_token=new_refresh_data,
            )
            
        except Exception as e:
            logger.error(f"Registration saga failed with error: {e}. Starting compensation...")
            await self._compensate_saga(saga)
            logger.info("Compensation completed")
            raise e

    async def _compensate_saga(self, saga: RegistrationSaga):
        """Откатываем выполненные шаги"""
        logger.info("Starting saga compensation")
        
        if saga.character_step_status == SagaStepStatus.COMPLETED and saga.character_id:
            try:
                logger.info(f"Compensating character creation for ID: {saga.character_id}")
                await self.character_client.delete(saga.character_id)
                saga.character_step_status = SagaStepStatus.COMPENSATED
                logger.info(f"Character {saga.character_id} compensated successfully")
            except Exception as e:
                logger.error(f"Failed to compensate character creation for ID {saga.character_id}: {e}")
        
        # Компенсируем создание пользователя
        if saga.user_step_status == SagaStepStatus.COMPLETED and saga.user_id:
            try:
                logger.info(f"Compensating user creation for ID: {saga.user_id}")
                await self.user_client.delete(saga.user_id)
                saga.user_step_status = SagaStepStatus.COMPENSATED
                logger.info(f"User {saga.user_id} compensated successfully")
            except Exception as e:
                logger.error(f"Failed to compensate user creation for ID {saga.user_id}: {e}")
        
        logger.info("Saga compensation process finished")