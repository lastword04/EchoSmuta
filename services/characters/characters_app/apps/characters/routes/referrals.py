"""Реферальная ссылка персонажа."""
from fastapi import APIRouter, Depends

from shared.schemas.auth import UserTokenDataReadSchema

from ..schemas import ReferralLinkResponseSchema
from ..use_cases.referrals.get_referral_link import GetReferralLinkUseCaseProtocol
from ....core.depends import get_user_token_payload
from ..deps import get_referral_link_use_case_dep

router = APIRouter()


@router.get('/referral-link', response_model=ReferralLinkResponseSchema)
async def get_referral_link(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetReferralLinkUseCaseProtocol = Depends(get_referral_link_use_case_dep)
) -> ReferralLinkResponseSchema:
    return await use_case(token)
