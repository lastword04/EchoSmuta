from typing_extensions import Self
from shared.schemas.characters import CharacterMultCreateSchema, CharacterReadSchema, CharacterCreateSchema
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 


class CreateCharacterMultUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self: Self, data: CharacterMultCreateSchema, token: UserTokenDataReadSchema) -> CharacterReadSchema:
        ...


class CreateCharacterMultUseCase(CreateCharacterMultUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: CharacterMultCreateSchema, token: UserTokenDataReadSchema) -> CharacterReadSchema:
        character_for_create = CharacterCreateSchema(
            user_id=token.user_id,
            **data.model_dump()
        )
        return await self.service.create_default(character_for_create)
