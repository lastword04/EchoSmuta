import uuid
from fastapi import APIRouter, Depends, Path
from shared.schemas.auth import UserTokenDataReadSchema
from ...core.depends import get_user_token_payload
from .schemas import (
    NotebookUpdateSchema,
    NotebookReadSchema
)
from .use_cases.update import UpdateNotebookUseCaseProtocol
from .use_cases.get_my import GetMyNotebookUseCaseProtocol
from .depends import (
    get_notebook_update_use_case,
    get_notebook_get_my_use_case
)

router = APIRouter(prefix='/api/notebook', tags=['Notebook'])

@router.get('/my', response_model=NotebookReadSchema)
async def get_my_notebook(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyNotebookUseCaseProtocol = Depends(get_notebook_get_my_use_case)
) -> NotebookReadSchema:
    return await use_case(user.character_id)


@router.put('/{notebook_id}', response_model=NotebookReadSchema)
async def update_notebook(
    data: NotebookUpdateSchema,
    notebook_id: uuid.UUID = Path(..., description="Id notebook for update"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateNotebookUseCaseProtocol = Depends(get_notebook_update_use_case)
) -> NotebookReadSchema:
    return await use_case(notebook_id=notebook_id, data=data, character_id=user.character_id)

