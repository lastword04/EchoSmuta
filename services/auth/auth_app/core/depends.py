from fastapi import Depends
from shared.services.tokens_utils import (
    DecodeAccessTokenProtocol, DecodeAccessTokenService,
)
from shared.depends import access_token_schema
from shared.schemas.auth import UserTokenDataReadSchema
from ..settings import Settings, get_settings


def get_decode_token_service(
        settings: Settings = Depends(get_settings)
) -> DecodeAccessTokenProtocol:
    """
    Декодирует токен доступа и возвращает данные пользователя.
    
    :param token: JWT токен доступа
    :param decode_service_token: Сервис для декодирования токена
    """
    return DecodeAccessTokenService(
        secret_key=settings.user_access_token.secret_key,
        algorithm=settings.user_access_token.algorithm
    )

def get_user_token_payload(token: str = Depends(access_token_schema),
                              decode_service_token: DecodeAccessTokenProtocol = Depends(get_decode_token_service)) -> UserTokenDataReadSchema:
    return decode_service_token.decode_access_token(token)