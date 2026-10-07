from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import ResourceReadSchema
from ...services.resources import ResourceServiceProtocol


class GetBySlugUseCaseProtocol(UseCaseProtocol[ResourceReadSchema]):
    async def __call__(self, slug: str, user: UserTokenDataReadSchema) -> ResourceReadSchema:
        ...

class GetBySlugUseCase(GetBySlugUseCaseProtocol):
    def __init__(self, service: ResourceServiceProtocol):
        self.service = service

    async def __call__(self, slug: str, user: UserTokenDataReadSchema) -> ResourceReadSchema:
        if not user.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_by_slug(slug)