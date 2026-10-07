from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import SessionUsersEvent
from ..schemas import SessionUserEventCreateSchema, SessionUserEventUpdateSchema, SessionUserEventReadSchema


class SessionUsersEventRepositoryProtocol(
    BaseRepositoryImpl[
        SessionUsersEvent,
        SessionUserEventReadSchema,
        SessionUserEventCreateSchema,
        SessionUserEventUpdateSchema
    ]
):
    pass


class SessionUsersEventRepository(SessionUsersEventRepositoryProtocol):
    pass