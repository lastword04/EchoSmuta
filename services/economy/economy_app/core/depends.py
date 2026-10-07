from fastapi import Depends
from shared.depends import access_token_schema
from shared.schemas.auth import UserTokenDataReadSchema
from shared.services.tokens_utils import DecodeAccessTokenService

from ..settings import settings


def get_user_token_payload(token: str = Depends(access_token_schema)) -> UserTokenDataReadSchema:
    return DecodeAccessTokenService(secret_key=settings.user_access_token.secret_key, algorithm=settings.user_access_token.algorithm).decode_access_token(token)
