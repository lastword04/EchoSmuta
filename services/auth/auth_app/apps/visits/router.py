from fastapi import APIRouter, Depends, Request
from .use_cases.create import NewUsersVisitUseCaseProtocol
from .depends import get_new_users_visit_use_case
from .schemas import NewUsersVisitRequestSchema, NewUsersVisitReadSchema

router = APIRouter(prefix='/api/visits', tags=['Visits'])

@router.post('/', response_model=NewUsersVisitReadSchema)
async def create_new_user_visit(
    request: Request,
    body: NewUsersVisitRequestSchema,
    use_case: NewUsersVisitUseCaseProtocol = Depends(get_new_users_visit_use_case)
) -> NewUsersVisitReadSchema:
    return await use_case(request, body)
