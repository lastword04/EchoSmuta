from shared.services.tokens_utils import (
    DecodeAccessTokenProtocol
)
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError

class ValidTokenUseCaseProtocol(UseCaseProtocol[UserTokenDataReadSchema]):
    async def __call__(self, token: str) -> UserTokenDataReadSchema:
        ...

class ValidTokenUseCase(ValidTokenUseCaseProtocol):
    def __init__(self, decoder: DecodeAccessTokenProtocol):
        self.decoder = decoder

    async def __call__(self, token: str) -> UserTokenDataReadSchema:
        user_data = self.decoder.decode_access_token(token)
        if not user_data.character_id:
            raise PermissionDeniedError()
        
        return user_data
