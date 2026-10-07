import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.info.characters_info import CharacterInfoServiceProtocol
from ...schemas import CharacterInfoReadSchema, CharacterInfoRequestSchema

class UpdateMyCharactersInfoUseCaseProtocol(UseCaseProtocol[CharacterInfoReadSchema]):
    async def __call__(self, info_id: uuid.UUID, info_data: CharacterInfoRequestSchema, 
                       token: UserTokenDataReadSchema) -> CharacterInfoReadSchema:
        ...

class UpdateMyCharacterInfoUseCase(UpdateMyCharactersInfoUseCaseProtocol):
    def __init__(self, service: CharacterInfoServiceProtocol):
        self.service = service

    async def __call__(self, info_id: uuid.UUID, info_data: CharacterInfoRequestSchema, 
                       token: UserTokenDataReadSchema) -> CharacterInfoReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.update_by_character_id(info_id, info_data, token.character_id)