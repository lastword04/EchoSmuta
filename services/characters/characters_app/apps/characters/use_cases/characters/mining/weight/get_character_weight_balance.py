import uuid
from typing_extensions import Self
from shared.schemas.characters import CharacterWeightBalance
from .......core.use_cases import UseCaseProtocol
from .....services.character.characters import CharacterWeightBalanceServiceProtocol


class GetCharacterWeightBalanceUseCaseProtocol(UseCaseProtocol[CharacterWeightBalance]):
    async def __call__(self: Self, character_id: uuid.UUID) -> CharacterWeightBalance:
        ...


class GetCharacterWeightBalanceUseCase(GetCharacterWeightBalanceUseCaseProtocol):
    def __init__(self: Self, service: CharacterWeightBalanceServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID) -> CharacterWeightBalance:
        weight_data = await self.service.get_weight_balance(character_id)
        return CharacterWeightBalance(**weight_data)
