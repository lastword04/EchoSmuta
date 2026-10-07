from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ....settings import Settings, get_settings
from ..repositories.referrals.referrals import (
    ReferralRepositoryProtocol,
    ReferralRepository,
)
from ..repositories.referrals.referral_link import (
    ReferralLinkRepositoryProtocol,
    ReferralLinkRepository,
)
from ..services.referrals.referrals import (
    ReferralServiceProtocol,
    ReferralService,
)
from ..services.referrals.referral_link import (
    ReferralLinkServiceProtocol,
    ReferralLinkService,
)


def __get_referral_repository(session: AsyncSession = Depends(get_async_session)) -> ReferralRepositoryProtocol:
    """
    Функция для получения репозитория рефералов.
    """
    return ReferralRepository(session=session)


def get_referral_service_dep(repository: ReferralRepositoryProtocol = Depends(__get_referral_repository)) -> ReferralServiceProtocol:
    return ReferralService(repository=repository)


def __get_referral_link_repository_dep(session: AsyncSession = Depends(get_async_session)) -> ReferralLinkRepositoryProtocol:
    """
    Функция для получения репозитория реферальных ссылок.
    """
    return ReferralLinkRepository(session=session)


def get_referral_link_service_dep(repository: ReferralLinkRepositoryProtocol = Depends(__get_referral_link_repository_dep),
                                    referral_service: ReferralServiceProtocol = Depends(get_referral_service_dep),
                                 settings: Settings = Depends(get_settings)) -> ReferralLinkServiceProtocol:
    return ReferralLinkService(repository=repository, referral_service=referral_service, frontend_url=settings.frontend_url)
