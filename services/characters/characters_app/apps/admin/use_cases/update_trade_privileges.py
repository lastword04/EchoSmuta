import uuid

from ....core.use_cases import UseCaseProtocol
from ...characters.schemas import CharacterTradePrivilegeReadSchema, CharacterTradePrivilegeUpdateSchema
from ...characters.services.trade_privileges.trade_privileges import CharacterTradePrivilegeServiceProtocol


class UpdateCharacterTradePrivilegesUseCaseProtocol(UseCaseProtocol[CharacterTradePrivilegeReadSchema]):
    async def __call__(
        self,
        character_id: uuid.UUID,
        data: CharacterTradePrivilegeUpdateSchema,
        updated_by_admin_id: uuid.UUID | None,
    ) -> CharacterTradePrivilegeReadSchema: ...


class UpdateCharacterTradePrivilegesUseCase(UpdateCharacterTradePrivilegesUseCaseProtocol):
    def __init__(self, service: CharacterTradePrivilegeServiceProtocol) -> None:
        self.service = service

    async def __call__(
        self,
        character_id: uuid.UUID,
        data: CharacterTradePrivilegeUpdateSchema,
        updated_by_admin_id: uuid.UUID | None,
    ) -> CharacterTradePrivilegeReadSchema:
        return await self.service.update_gold_trade_enabled(
            character_id,
            data.gold_trade_enabled,
            updated_by_admin_id,
        )
