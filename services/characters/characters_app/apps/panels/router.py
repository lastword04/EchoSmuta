import uuid
from fastapi import APIRouter, Depends, Path
from shared.schemas.auth import UserTokenDataReadSchema
from ...core.depends import get_user_token_payload
from .schemas import (
    CharacterFastItemReadSchema,
    CharacterFastItemUpdateSchema
)
from .use_cases.update import UpdateItemsUseCaseProtocol
from .use_cases.get_my import GetMyItemsUseCaseProtocol
from .depends import (
    get_item_update_use_case,
    get_item_get_my_use_case
)

router = APIRouter(prefix='/api/panels', tags=['Panels'])

@router.get('/my', response_model=CharacterFastItemReadSchema)
async def get_my_items(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyItemsUseCaseProtocol = Depends(get_item_get_my_use_case)
) -> CharacterFastItemReadSchema:
    return await use_case(user)


@router.put('/{items_id}', response_model=CharacterFastItemReadSchema)
async def update_notebook(
    data: CharacterFastItemUpdateSchema,
    items_id: uuid.UUID = Path(..., description="Id items for update"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateItemsUseCaseProtocol = Depends(get_item_update_use_case)
) -> CharacterFastItemReadSchema:
    return await use_case(items_id=items_id, data=data, character=user)

