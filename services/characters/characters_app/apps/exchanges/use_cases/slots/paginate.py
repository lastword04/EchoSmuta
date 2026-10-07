from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import PaginationSchema
from .....core.use_cases import UseCaseProtocol 
from ...schemas import SlotPaginationResultSchema
from ...services.slots import GetSlotsServiceProtocol 
from ...enums import Currency


class GetPaginatedSlotsUseCaseProtocol(UseCaseProtocol[SlotPaginationResultSchema]):
    async def __call__(self: Self, limit: int, offset: int, buy_for: Currency, token: UserTokenDataReadSchema) -> SlotPaginationResultSchema:
        ...


class GetPaginatedSlotsUseCase(GetPaginatedSlotsUseCaseProtocol):
    def __init__(self: Self, service: GetSlotsServiceProtocol):
        self.service = service

    async def __call__(self: Self, limit: int, offset: int, buy_for: Currency, token: UserTokenDataReadSchema) -> SlotPaginationResultSchema:
        paginate_schema = PaginationSchema(limit=limit, offset=offset)
        return await self.service.paginate(paginate_schema, buy_for, token.user_id)
