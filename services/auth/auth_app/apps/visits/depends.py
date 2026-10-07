from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from .repositories.visits import NewUsersVisitRepositoryProtocol, NewUsersVisitRepository
from .repositories.sessions import SessionUsersEventRepositoryProtocol, SessionUsersEventRepository
from .services.visits import NewUsersVisitServiceProtocol, NewUsersVisitService
from .services.sessions import SessionUsersEventServiceProtocol, SessionUsersEventService
from .use_cases.create import NewUsersVisitUseCaseProtocol, NewUsersVisitUseCase

def __get_new_users_visit_repository(
    session: AsyncSession = Depends(get_async_session)
) -> NewUsersVisitRepositoryProtocol:
    return NewUsersVisitRepository(session=session)

def get_new_users_visit_service(
    repository: NewUsersVisitRepositoryProtocol = Depends(__get_new_users_visit_repository)
) -> NewUsersVisitServiceProtocol:
    return NewUsersVisitService(repository=repository)

def get_new_users_visit_use_case(
    service: NewUsersVisitServiceProtocol = Depends(get_new_users_visit_service)
) -> NewUsersVisitUseCaseProtocol:
    return NewUsersVisitUseCase(service=service)

def __get_session_users_event_repository(
    session: AsyncSession = Depends(get_async_session)
) -> SessionUsersEventRepositoryProtocol:
    return SessionUsersEventRepository(session=session)

def get_session_users_event_service(
    repository: SessionUsersEventRepositoryProtocol = Depends(__get_session_users_event_repository)
) -> SessionUsersEventServiceProtocol:
    return SessionUsersEventService(repository=repository)