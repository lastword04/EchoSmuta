import uuid

from ...schemas import CharacterTradePrivilegesInternalSchema
from ...services.trade_privileges.trade_privileges import CharacterTradePrivilegeServiceProtocol
from ...adapters.mining import MiningServiceClientProtocol
from .....core.use_cases import UseCaseProtocol


class GetCharacterTradePrivilegesUseCaseProtocol(UseCaseProtocol[CharacterTradePrivilegesInternalSchema]):
    async def __call__(self, character_id: uuid.UUID) -> CharacterTradePrivilegesInternalSchema: ...


class GetCharacterTradePrivilegesUseCase(GetCharacterTradePrivilegesUseCaseProtocol):
    def __init__(
        self,
        service: CharacterTradePrivilegeServiceProtocol,
        mining_client: MiningServiceClientProtocol,
    ) -> None:
        self.service = service
        self.mining_client = mining_client

    async def __call__(self, character_id: uuid.UUID) -> CharacterTradePrivilegesInternalSchema:
        db_enabled = await self.service.get_gold_trade_enabled(character_id)
        print(f"🔑 [use_case] db_enabled={db_enabled}")
        license_active = await self.mining_client.has_active_trade_license(character_id)
        print(f"🔑 [use_case] license_active={license_active}")
        result = db_enabled or license_active
        print(f"🔑 [use_case] FINAL result={result}")
        return CharacterTradePrivilegesInternalSchema(gold_trade_enabled=result)