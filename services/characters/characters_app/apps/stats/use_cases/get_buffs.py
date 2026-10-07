import uuid
from ....core.use_cases import UseCaseProtocol
from ..schemas import CharacterBuffsResponseSchema
from ..services.buff_service import BuffServiceProtocol


class GetCharacterBuffsUseCaseProtocol(UseCaseProtocol[CharacterBuffsResponseSchema]):
    async def __call__(self, character_id: uuid.UUID) -> CharacterBuffsResponseSchema: ...


class GetCharacterBuffsUseCase(GetCharacterBuffsUseCaseProtocol):
    def __init__(self, service: BuffServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID) -> CharacterBuffsResponseSchema:
        buffs = await self.service.get_character_buffs(character_id)
        return CharacterBuffsResponseSchema(
            character_id=character_id,
            buffs=buffs
        )