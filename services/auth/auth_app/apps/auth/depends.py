import redis.asyncio as redis
from fastapi import Depends
from typing import Callable
from ...settings import get_settings, Settings
from ...core.db import AsyncSession, get_async_session
from ...core.redis import get_redis_client
from ..visits.services.visits import NewUsersVisitServiceProtocol
from ..visits.services.sessions import SessionUsersEventServiceProtocol
from ..visits.depends import get_new_users_visit_service, get_session_users_event_service
from .repositories.refresh_tokens import RefreshTokenRepositoryProtocol, RefreshTokenRepository
from .repositories.reset_tokens import ResetTokenRepositoryProtocol, ResetTokenRepository
from .repositories.auth_logs import AuthLogRepositoryProtocol, AuthLogRepository
from .adapters.users import UserServiceClientProtocol, UserServiceClient
from .adapters.characters import CharacterServiceClientProtocol, CharacterServiceClient
from .adapters.emails import EmailServiceClientProtocol, EmailServiceClient
from .adapters.captcha import CaptchaServiceClientProtocol, CaptchaServiceClient
from .events.publisher import RedisPublisherProtocol, RedisPublisher
from .events.characters import CharacterEventsProtocol, CharacterEvents
from .events.subscriber import RedisSubscriber, RedisSubscriberProtocol
from .events.character_event_handlers import AuthCharacterEventHandler, AuthCharacterEventHandlerProtocol
from .services.auth import AuthServiceProtocol, AuthService
from .services.tokens import (
    ResetTokenServiceProtocol, ResetTokenService, 
    CleanupResetPasswordServiceProtocol, CleanupResetPasswordService,
    TokenServiceProtocol, TokenService,
    CleanupRefreshTokenServiceProtocol, CleanupRefreshTokenService
)
from .services.reset_passwords import ResetPasswordServiceProtocol, ResetPasswordService
from .services.passwords import PasswordServiceProtocol, PasswordService
from .use_cases.register import RegisterUseCaseProtocol, RegisterUseCase
from .use_cases.login import LoginUseCaseProtocol, LoginUseCase
from .use_cases.refresh import RefreshUseCaseProtocol, RefreshUseCase
from .use_cases.logout import LogoutUseCaseProtocol, LogoutUseCase
from .use_cases.reset_password import ResetPasswordUseCaseProtocol, ResetPasswordUseCase
from .use_cases.confirm_password import ConfirmPasswordUseCaseProtocol, ConfirmPasswordUseCase
from .use_cases.login_to_forum import LoginForumUseCaseProtocol, LoginForumUseCase
from .use_cases.clean_expired_reset_tokens import CleanupResetTokenUseCaseProtocol, CleanupResetTokenUseCase
from .use_cases.clean_expired_refresh_tokens import CleanupRefreshTokenUseCaseProtocol, CleanupRefreshTokenUseCase
from .use_cases.play import PlayUseCaseProtocol, PlayUseCase
from .use_cases.play_main import PlayMainUseCaseProtocol, PlayMainUseCase
from .use_cases.quit import QuitUseCaseProtocol, QuitUseCase
from .use_cases.log_auth_attempt import LogAuthAttemptUseCaseProtocol, LogAuthAttemptUseCase

def get_redis_publisher(redis: redis.Redis = Depends(get_redis_client)) -> RedisPublisherProtocol:
    return RedisPublisher(redis)

def get_character_event(publisher: RedisPublisherProtocol = Depends(get_redis_publisher)) -> CharacterEventsProtocol:
    return CharacterEvents(publisher)

def get_auth_log_repository(session: AsyncSession = Depends(get_async_session)) -> AuthLogRepositoryProtocol:
    return AuthLogRepository(session=session)

def get_log_auth_attempt_use_case(
    repository: AuthLogRepositoryProtocol = Depends(get_auth_log_repository)
) -> LogAuthAttemptUseCaseProtocol:
    return LogAuthAttemptUseCase(repository=repository)

def __get_refresh_token_repository(session: AsyncSession = Depends(get_async_session),
                                   settings: Settings = Depends(get_settings)) -> RefreshTokenRepositoryProtocol:
    return RefreshTokenRepository(session=session, expire_minutes=settings.refresh_token.expire_minutes)

def get_user_service_client(settings: Settings = Depends(get_settings), timeout: float = 120.0) -> UserServiceClientProtocol:
    return UserServiceClient(base_url=settings.user_service_app.base_url, timeout=timeout)

def get_character_service_client(settings: Settings = Depends(get_settings), timeout: float = 120.0) -> CharacterServiceClientProtocol:
    return CharacterServiceClient(base_url=settings.character_service_app.base_url, timeout=timeout)

def get_captcha_service_client(settings: Settings = Depends(get_settings), timeout: float = 120.0) -> CaptchaServiceClientProtocol:
    return CaptchaServiceClient(base_url=settings.captcha_service_app.base_url, timeout=timeout)

def get_token_service(settings: Settings = Depends(get_settings),
                      refresh_token_repository: RefreshTokenRepositoryProtocol = Depends(__get_refresh_token_repository)
                      ) -> TokenServiceProtocol:
    return TokenService(
        refresh_token_repository=refresh_token_repository,
        secret_key=settings.user_access_token.secret_key,
        algorithm=settings.user_access_token.algorithm,
        access_token_expire_minutes=settings.user_access_token.expire_minutes,
        refresh_token_expire_minutes=settings.refresh_token.expire_minutes
    )

def get_auth_service(
    user_client: UserServiceClientProtocol = Depends(get_user_service_client),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    captcha_client: CaptchaServiceClientProtocol = Depends(get_captcha_service_client),
    token_service: TokenServiceProtocol = Depends(get_token_service),
    character_event: CharacterEventsProtocol = Depends(get_character_event),
    visit_service: NewUsersVisitServiceProtocol = Depends(get_new_users_visit_service),
    session_service: SessionUsersEventServiceProtocol = Depends(get_session_users_event_service),
    log_auth_use_case: LogAuthAttemptUseCaseProtocol = Depends(get_log_auth_attempt_use_case),
) -> AuthServiceProtocol:
    return AuthService(
        user_client=user_client,
        character_client=character_client,
        captcha_client=captcha_client,
        token_service=token_service,
        character_event=character_event,
        visit_service=visit_service,
        session_service=session_service,
        log_auth_use_case=log_auth_use_case,
    )

def get_register_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> RegisterUseCaseProtocol:
    return RegisterUseCase(service=auth_service)

def get_login_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> LoginUseCaseProtocol:
    return LoginUseCase(service=auth_service)

def get_refresh_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> RefreshUseCaseProtocol:
    return RefreshUseCase(service=auth_service)


def get_logout_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> LogoutUseCaseProtocol:
    return LogoutUseCase(service=auth_service)


def __get_reset_token_repository(session: AsyncSession = Depends(get_async_session),
                                 settings: Settings = Depends(get_settings)) -> ResetTokenRepositoryProtocol:
    return ResetTokenRepository(session=session, expire_minutes=settings.reset_token.expire_minutes)


def get_password_service() -> PasswordServiceProtocol:
    return PasswordService()

def get_reset_token_service(reset_token_repository: ResetTokenRepositoryProtocol = Depends(__get_reset_token_repository),
                            password_service: PasswordServiceProtocol = Depends(get_password_service),
                                    settings: Settings = Depends(get_settings)) -> ResetTokenServiceProtocol:
    return ResetTokenService(
        password_reset_repository=reset_token_repository,
        password_service=password_service,
        expire_minutes=settings.reset_token.expire_minutes
    )

def get_email_client(settings: Settings = Depends(get_settings)) -> EmailServiceClientProtocol:
    return EmailServiceClient(base_url=settings.email_service_app.base_url)

def get_reset_password_service(user_service: UserServiceClientProtocol = Depends(get_user_service_client),
                               mail_sender: EmailServiceClientProtocol = Depends(get_email_client),
                               reset_token_service: ResetTokenServiceProtocol = Depends(get_reset_token_service),
                               token_service: TokenServiceProtocol = Depends(get_token_service),
                               settings: Settings = Depends(get_settings)) -> ResetPasswordServiceProtocol:
    return ResetPasswordService(
        user_service=user_service,
        mail_sender=mail_sender,
        reset_password_token_service=reset_token_service,
        token_service=token_service,
        settings=settings
    )

def get_confirm_password_use_case(reset_password_service: ResetPasswordServiceProtocol = Depends(get_reset_password_service)) -> ConfirmPasswordUseCaseProtocol:
    return ConfirmPasswordUseCase(service=reset_password_service)

def get_reset_password_use_case(reset_password_service: ResetPasswordServiceProtocol = Depends(get_reset_password_service)) -> ResetPasswordUseCaseProtocol:
    return ResetPasswordUseCase(service=reset_password_service)


def get_login_forum_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> LoginForumUseCaseProtocol:
    return LoginForumUseCase(service=auth_service)

def get_play_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> PlayUseCaseProtocol:
    return PlayUseCase(auth_service)

def get_play_main_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> PlayMainUseCaseProtocol:
    return PlayMainUseCase(auth_service)


def get_quit_use_case(auth_service: AuthServiceProtocol = Depends(get_auth_service)) -> QuitUseCaseProtocol:
    return QuitUseCase(auth_service)

def get_cleanup_reset_token_service(reset_password_repository: ResetTokenRepositoryProtocol = Depends(__get_reset_token_repository)) -> CleanupResetPasswordServiceProtocol:
    return CleanupResetPasswordService(password_reset_repository=reset_password_repository)

def get_cleanup_reset_token_use_case(session: AsyncSession, settings: Settings) -> CleanupResetTokenUseCaseProtocol:
    repo = __get_reset_token_repository(session=session, settings=settings)
    cleanup_service = get_cleanup_reset_token_service(reset_password_repository=repo)
    return CleanupResetTokenUseCase(service=cleanup_service)

def get_cleanup_refresh_token_service(refresh_token_repository: RefreshTokenRepositoryProtocol = Depends(__get_refresh_token_repository)) -> CleanupRefreshTokenServiceProtocol:
    return CleanupRefreshTokenService(refresh_token_repository=refresh_token_repository)

def get_cleanup_refresh_token_use_case(session: AsyncSession, settings: Settings) -> CleanupRefreshTokenUseCaseProtocol:
    repo = __get_refresh_token_repository(session=session, settings=settings)
    cleanup_service = get_cleanup_refresh_token_service(refresh_token_repository=repo)
    return CleanupRefreshTokenUseCase(service=cleanup_service)

def get_redis_subscriber(redis_client: redis.Redis = Depends(get_redis_client)) -> RedisSubscriberProtocol:
    return RedisSubscriber(redis_client)


def create_token_service_factory(settings: Settings) -> Callable[[AsyncSession], TokenServiceProtocol]:
    def factory(session: AsyncSession) -> TokenServiceProtocol:
        return TokenService(
            refresh_token_repository=RefreshTokenRepository(
                session=session,
                expire_minutes=settings.refresh_token.expire_minutes
            ),
            secret_key=settings.user_access_token.secret_key,
            algorithm=settings.user_access_token.algorithm,
            access_token_expire_minutes=settings.user_access_token.expire_minutes,
            refresh_token_expire_minutes=settings.refresh_token.expire_minutes,
        )
    return factory


def get_token_service_factory(
    settings: Settings = Depends(get_settings),
) -> Callable[[AsyncSession], TokenServiceProtocol]:
    return create_token_service_factory(settings)


def get_auth_character_event_handler(
    subscriber: RedisSubscriberProtocol = Depends(get_redis_subscriber),
    token_service_factory: Callable[[AsyncSession], TokenServiceProtocol] = Depends(get_token_service_factory),
) -> AuthCharacterEventHandlerProtocol:
    return AuthCharacterEventHandler(subscriber=subscriber, token_service_factory=token_service_factory)
