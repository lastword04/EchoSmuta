import uuid
import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from typing import Optional
from typing_extensions import Self
from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import ReferralLink
from ...schemas import (
    ReferralLinkCreateSchema, ReferralLinkUpdateDBSchema, 
    ReferralLinkReadSchema, ReferralLinkWithReferralsReadSchema
)

class ReferralLinkRepositoryProtocol(BaseRepositoryImpl[
    ReferralLink,
    ReferralLinkReadSchema,
    ReferralLinkCreateSchema,
    ReferralLinkUpdateDBSchema
]):
    async def get_by_code(self: Self, referral_code: str) -> Optional[ReferralLinkReadSchema]:
        pass

    async def get_by_referrer_id(self: Self, referrer_id: uuid.UUID) -> ReferralLinkReadSchema:
        pass


class ReferralLinkRepository(ReferralLinkRepositoryProtocol):
    """
    Repository for managing referral links.
    This class implements the protocol for handling referral link operations.
    """
    async def get_by_code(self: Self, referral_code: str) -> Optional[ReferralLinkReadSchema]:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.referral_code == referral_code,
                    self.model_type.is_active
                )
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            if model is None:
                return None        
            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def get_by_referrer_id(self: Self, referrer_id: uuid.UUID) -> ReferralLinkWithReferralsReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .options(selectinload(self.model_type.referrals))
                .where(
                    self.model_type.referrer_id == referrer_id,
                    self.model_type.is_active
                )
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            if not model:
                raise ModelFieldNotFoundException(self.model_type, "referrer_id", referrer_id)
        
            return ReferralLinkWithReferralsReadSchema.model_validate(model, from_attributes=True)