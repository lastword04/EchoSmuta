from fastapi import APIRouter, Depends, Response, Path, Cookie, Request
import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterReadSchema
from shared.depends import refresh_token_schema
from ...core.depends import get_user_token_payload
from .use_cases.register import RegisterUseCaseProtocol
from .use_cases.login import LoginUseCaseProtocol
from .use_cases.refresh import RefreshUseCaseProtocol
from .use_cases.logout import LogoutUseCaseProtocol
from .use_cases.reset_password import ResetPasswordUseCaseProtocol
from .use_cases.confirm_password import ConfirmPasswordUseCaseProtocol
from .use_cases.login_to_forum import LoginForumUseCaseProtocol
from .use_cases.play import PlayUseCaseProtocol
from .use_cases.play_main import PlayMainUseCaseProtocol
from .use_cases.quit import QuitUseCaseProtocol
from .depends import (
    get_register_use_case,
    get_login_use_case,
    get_refresh_use_case,
    get_logout_use_case,
    get_reset_password_use_case,
    get_confirm_password_use_case,
    get_login_forum_use_case,
    get_play_use_case,
    get_play_main_use_case,
    get_quit_use_case
)
from .schemas import (
    UserAndCharacterCreateSchema, LoginSchema,
    UserAndCharacterSimpleReadSchema, ResetPasswordRequest, 
    UserResetSchema, TokenReadSchema, SessionUserEventRequestSchema
)
from .utils.cookies import set_auth_cookies

router = APIRouter(prefix='/api/auth', tags=['Auth'])


@router.post('/register', response_model=CharacterReadSchema, status_code=201)
async def register_user_and_character(request: Request,
    user_and_character: UserAndCharacterCreateSchema, 
                                      response: Response,
                                      use_case: RegisterUseCaseProtocol = Depends(get_register_use_case)
                                      ) -> CharacterReadSchema:
    result = await use_case(request, user_and_character)
    
    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return result.character


@router.post('/login', response_model=UserAndCharacterSimpleReadSchema, status_code=200)
async def login_user(login_data: LoginSchema, 
                     request: Request,
                     response: Response, 
                     use_case: LoginUseCaseProtocol = Depends(get_login_use_case)) -> UserAndCharacterSimpleReadSchema:
    result = await use_case(request, login_data)

    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return result.to_user_and_character_read_schema()

@router.post('/login-forum', response_model=UserAndCharacterSimpleReadSchema, status_code=200)
async def login_forum(login_data: LoginSchema, 
                     response: Response, 
                     use_case: LoginForumUseCaseProtocol = Depends(get_login_forum_use_case)) -> UserAndCharacterSimpleReadSchema:
    result = await use_case(login_data)

    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return result.to_user_and_character_read_schema()

@router.get('/token', response_model=TokenReadSchema)
async def get_token(
    access_token: str = Cookie(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> TokenReadSchema:
    return TokenReadSchema(
        token=access_token,
        expiration=user.expiration
    )


@router.post('/refresh', response_model=UserAndCharacterSimpleReadSchema, status_code=200)
async def refresh_user_tokens(response: Response, refresh_token: str = Depends(refresh_token_schema),
                              use_case: RefreshUseCaseProtocol = Depends(get_refresh_use_case)) -> UserAndCharacterSimpleReadSchema:
    result = await use_case(refresh_token)

    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return result.to_user_and_character_read_schema()

@router.post("/logout", response_model=None, status_code=204)
async def logout(
    response: Response,
    request: Request,
    session_request: SessionUserEventRequestSchema,
    logout: LogoutUseCaseProtocol = Depends(get_logout_use_case),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    refresh_token: str = Depends(refresh_token_schema)
):
    await logout(request, session_request, user, refresh_token)
    
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    
    return None

@router.post('/reset-password', response_model=None, status_code=204)
async def reset_password(
    reset_password_data: UserResetSchema,
    use_case: ResetPasswordUseCaseProtocol = Depends(get_reset_password_use_case)
):
    await use_case(reset_password_data)
    return None

@router.post('/confirm-reset-password', response_model=None, status_code=204)
async def confirm_reset_password(
    reset_password_request: ResetPasswordRequest,
    use_case: ConfirmPasswordUseCaseProtocol = Depends(get_confirm_password_use_case)
):
    await use_case(reset_password_request)
    return None

@router.post('/characters/main/play', response_model=CharacterReadSchema)
async def play_main(
    response: Response,
    request: Request,
    session_request: SessionUserEventRequestSchema,
    refresh_token: str = Depends(refresh_token_schema),
    user_token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: PlayMainUseCaseProtocol = Depends(get_play_main_use_case)
) -> CharacterReadSchema:
    
    result = await use_case(request, session_request, user_token, refresh_token)

    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return result.character

@router.post('/characters/{character_id}/play', response_model=CharacterReadSchema)
async def play(
    response: Response,
    request: Request,
    session_request: SessionUserEventRequestSchema,
    refresh_token: str = Depends(refresh_token_schema),
    character_id: uuid.UUID = Path(..., description="Character for join to game"),
    user_token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: PlayUseCaseProtocol = Depends(get_play_use_case)
) -> CharacterReadSchema:
    
    result = await use_case(request, session_request, character_id, user_token, refresh_token)

    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return result.character

@router.post('/characters/{character_id}/quit', response_model=None, status_code=204)
async def quit(
    response: Response,
    request: Request,
    session_request: SessionUserEventRequestSchema,
    refresh_token: str = Depends(refresh_token_schema),
    character_id: uuid.UUID = Path(...),
    user_token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: QuitUseCaseProtocol = Depends(get_quit_use_case)
) -> None:
    result = await use_case(request, session_request, character_id, user_token, refresh_token)

    set_auth_cookies(response, result.access_token.token, result.refresh_token.token)

    return None
