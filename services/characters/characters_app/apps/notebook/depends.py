from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_async_session
from .repositories.notebook import NotebookRepositoryProtocol, NotebookRepository
from .services.notebook import NotebookCRUServiceProtocol, NotebookCRUService
from .use_cases.update import UpdateNotebookUseCaseProtocol, UpdateNotebookUseCase
from .use_cases.get_my import GetMyNotebookUseCaseProtocol, GetMyNotebookUseCase


def __get_notebook_repository(session: AsyncSession = Depends(get_async_session)) -> NotebookRepositoryProtocol:
    return NotebookRepository(session)


def get_notebook_service(repository: NotebookRepositoryProtocol = Depends(__get_notebook_repository)) -> NotebookCRUServiceProtocol:
    return NotebookCRUService(repository)


def get_notebook_update_use_case(notebook_service: NotebookCRUServiceProtocol = Depends(get_notebook_service)) -> UpdateNotebookUseCaseProtocol:
    return UpdateNotebookUseCase(notebook_service)


def get_notebook_get_my_use_case(notebook_service: NotebookCRUServiceProtocol = Depends(get_notebook_service)) -> GetMyNotebookUseCaseProtocol:
    return GetMyNotebookUseCase(notebook_service)