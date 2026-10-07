from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import UserAdditionalInformation
from ..schemas import (
    UserAdditionalInformationReadSchema,
    UserAdditionalInformationUpdateSchema,
    UserAdditionalInformationCreateSchema,
)


class UserAdditionalInfoRepositoryProtocol(
    BaseRepositoryImpl[
        UserAdditionalInformation,
        UserAdditionalInformationReadSchema,
        UserAdditionalInformationCreateSchema,
        UserAdditionalInformationUpdateSchema,
    ]
):
    pass


class UserAdditionalInfoRepository(UserAdditionalInfoRepositoryProtocol):
    pass
