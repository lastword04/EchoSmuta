from fastapi import Depends

from ...settings import settings
from .characters_client import CharactersClient
from .mining_client import MiningClient


def get_characters_client() -> CharactersClient:
    config = settings.characters_service
    jwt_config = settings.service_jwt
    return CharactersClient(
        base_url=config.base_url,
        secret_key=jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
        expire_minutes=jwt_config.expire_minutes,
        timeout=config.timeout
    )


def get_mining_client() -> MiningClient:
    config = settings.mining_service
    jwt_config = settings.service_jwt
    return MiningClient(
        base_url=config.base_url,
        secret_key=jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
        expire_minutes=jwt_config.expire_minutes,
        timeout=config.timeout
    )


CharactersClientDependency = Depends(get_characters_client)
MiningClientDependency = Depends(get_mining_client)
