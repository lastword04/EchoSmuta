import uuid
from pydantic import HttpUrl
from typing import Protocol, Optional
from typing_extensions import Self
from urllib.parse import urlencode, urljoin
from ...schemas import (
    ReferralLinkCreateSchema, ReferralLinkUpdateDBSchema, 
    ReferralLinkUpdateSchema, ReferralLinkReadSchema,
    ReferralCreateSchema, ReferralLinkWithReferralsAndUrlReadSchema
)
from ...repositories.referrals.referral_link import ReferralLinkRepositoryProtocol
from .referrals import ReferralServiceProtocol

class ReferralLinkServiceProtocol(Protocol):
    async def create_referral_link(self: Self, data: ReferralLinkCreateSchema) -> ReferralLinkReadSchema:
        pass

    async def update_referral_link(self: Self, id: uuid.UUID, data: ReferralLinkUpdateSchema) -> ReferralLinkReadSchema:
        pass

    async def get_referral_link_by_code(self: Self, referral_code: str) -> Optional[ReferralLinkReadSchema]:
        pass

    async def get_referral_link_by_referrer_id(self: Self, referrer_id: uuid.UUID) -> ReferralLinkWithReferralsAndUrlReadSchema:
        pass

    async def add_new_referral(self: Self, referred_user_id: uuid.UUID, referral_code: str) -> bool:
        """Add a new referral link for the given referrer."""
        pass


class ReferralLinkService(ReferralLinkServiceProtocol):
    def __init__(self, repository: ReferralLinkRepositoryProtocol,
                 referral_service: ReferralServiceProtocol,
                 frontend_url: HttpUrl):
        self.repository = repository
        self.referral_service = referral_service
        self.frontend_url = frontend_url

    async def create_referral_link(self: Self, data: ReferralLinkCreateSchema) -> ReferralLinkReadSchema:
        return await self.repository.create(data)

    async def update_referral_link(self: Self, id: uuid.UUID, data: ReferralLinkUpdateSchema) -> ReferralLinkReadSchema:
        db_update = ReferralLinkUpdateDBSchema(
            id=id,
            **data.model_dump()
        )
        return await self.repository.update(db_update)

    async def get_referral_link_by_code(self: Self, referral_code: str) -> Optional[ReferralLinkReadSchema]:
        return await self.repository.get_by_code(referral_code)

    async def get_referral_link_by_referrer_id(self: Self, referrer_id: uuid.UUID) -> ReferralLinkWithReferralsAndUrlReadSchema:
        referral_link = await self.repository.get_by_referrer_id(referrer_id)
        url = self._generate_referral_link_url(referral_link.referral_code)
        return ReferralLinkWithReferralsAndUrlReadSchema(
            **referral_link.model_dump(),
            url=url
        )
    
    async def add_new_referral(self: Self, referred_user_id: uuid.UUID, referral_code: str) -> bool:
        referral_link = await self.get_referral_link_by_code(referral_code)
        if not referral_link:
            return False
        referral = ReferralCreateSchema(
            referrer_id=referral_link.referrer_id,
            referred_user_id=referred_user_id,
            referral_link_id=referral_link.id
        )
        await self.referral_service.create_referral(referral)
        update_data = ReferralLinkUpdateSchema(
            current_uses=referral_link.current_uses + 1,
            **referral_link.model_dump(exclude={'current_uses', 'id', 'updated_at'})
        )
        await self.update_referral_link(referral_link.id, update_data)
        return True
    def _generate_referral_link_url(self: Self, referral_code: str) -> str:
        """Generate the full URL for the referral link."""
        # Create proper URL with encoded parameters
        base_url = urljoin(str(self.frontend_url), '/register')
        params = {'ref': referral_code}
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"