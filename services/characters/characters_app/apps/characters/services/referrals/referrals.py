import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.referrals.referrals import ReferralRepositoryProtocol
from ...schemas import (
    ReferralCreateSchema, 
    ReferralUpdateSchema,
    ReferralUpdateDBSchema,
    ReferralReadSchema
)

class ReferralServiceProtocol(Protocol):
    async def create_referral(self: Self, data: ReferralCreateSchema) -> ReferralReadSchema:
        pass

    async def update_referral(self: Self, id: uuid.UUID, data: ReferralUpdateSchema) -> ReferralReadSchema:
        pass

    async def get_referral_by_id(self: Self, id: uuid.UUID) -> ReferralReadSchema:
        pass

class ReferralService(ReferralServiceProtocol):
    def __init__(self, repository: ReferralRepositoryProtocol):
        self.repository = repository

    async def create_referral(self: Self, data: ReferralCreateSchema) -> ReferralReadSchema:
        return await self.repository.create(data)

    async def update_referral(self: Self, id: uuid.UUID, data: ReferralUpdateSchema) -> ReferralReadSchema:
        db_update = ReferralUpdateDBSchema(
            id=id,
            **data.model_dump()
        )
        return await self.repository.update(db_update)

    async def get_referral_by_id(self: Self, id: uuid.UUID) -> ReferralReadSchema:
        return await self.repository.get(id)

