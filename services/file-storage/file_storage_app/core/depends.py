from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from shared.services.tokens_utils import (
    DecodeTokenServiceProtocol, DecodeTokenService,
    DecodeAccessTokenProtocol, DecodeAccessTokenService
)
from shared.depends import access_token_schema
from shared.schemas.auth import UserTokenDataReadSchema

from ..settings import Settings, get_settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="any")


def get_decode_token(
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
                              decode_service_token: DecodeAccessTokenProtocol = Depends(get_decode_token)) -> UserTokenDataReadSchema:
    return decode_service_token.decode_access_token(token)


def get_decode_token_service(settings: Settings = Depends(get_settings)
) -> DecodeTokenServiceProtocol:
    """
    Provides a service for decoding access tokens.
    
    :param settings: Application settings containing JWT configuration.
    :return: DecodeTokenService instance configured with the secret key and algorithm.
    """
    return DecodeTokenService(
        secret_key=settings.service_jwt.secret_key,
        algorithm=settings.service_jwt.algorithm
    )

def get_service_token_payload(
        token: str = Depends(oauth2_scheme),
        settings: Settings = Depends(get_settings),
        decode_service_token: DecodeTokenServiceProtocol = Depends(get_decode_token_service)
) -> dict:
    """
    Декодирует сервисный токен и возвращает его полезную нагрузку.
    
    :param token: JWT сервисный токен
    :param decode_service_token: Сервис для декодирования токена
    :return: Полезная нагрузка токена
    """
    return decode_service_token.decode_service_token(token, expected_audience=settings.service_name)