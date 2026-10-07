import uuid

from .....core.use_cases import UseCaseProtocol
from ...schemas import CraftingLicenseReadSchema
from ...services.crafting_license.crafting_license import CraftingLicenseServiceProtocol


class RenewCraftingLicenseUseCaseProtocol(UseCaseProtocol[CraftingLicenseReadSchema]):
    async def __call__(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema: ...

class RenewCraftingLicenseUseCase(RenewCraftingLicenseUseCaseProtocol):
    def __init__(self, service: CraftingLicenseServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID, location_slug: str) -> CraftingLicenseReadSchema:
        return await self.service.renew_license(character_id, location_slug)