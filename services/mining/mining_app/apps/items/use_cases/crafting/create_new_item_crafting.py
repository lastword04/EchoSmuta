import uuid

from shared.schemas.captcha import CaptchaVerificationRequest

from .....core.use_cases import UseCaseProtocol
from ...schemas import ItemsCreatingActionReadSchema
from ...services.crafting.items_creating_actions import (
    ValidateCreateItemActionServiceProtocol,
)


class CreateNewItemCraftingUseCaseProtocol(UseCaseProtocol[ItemsCreatingActionReadSchema]):
    async def __call__(
        self,
        character_id: uuid.UUID,
        recipe_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        ...


class CreateNewItemCraftingUseCase(CreateNewItemCraftingUseCaseProtocol):
    def __init__(self, service: ValidateCreateItemActionServiceProtocol):
        self.service = service

    async def __call__(
        self,
        character_id: uuid.UUID,
        recipe_id: uuid.UUID,
        captcha: CaptchaVerificationRequest
    ) -> ItemsCreatingActionReadSchema:
        return await self.service.validate_captcha_and_create_new_item(
            character_id=character_id,
            recipe_id=recipe_id,
            captcha=captcha
        )
