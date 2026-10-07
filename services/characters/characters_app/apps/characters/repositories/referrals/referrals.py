from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import Referral
from ...schemas import (
    ReferralCreateSchema, ReferralUpdateDBSchema,
    ReferralReadSchema
)

class ReferralRepositoryProtocol(BaseRepositoryImpl[
    Referral,
    ReferralReadSchema,
    ReferralCreateSchema,
    ReferralUpdateDBSchema
]):
    pass

class ReferralRepository(ReferralRepositoryProtocol):
    pass