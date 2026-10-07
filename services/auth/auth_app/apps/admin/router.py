from fastapi import APIRouter, Depends

from .depends import get_auth_logs_use_case, require_admin
from .schemas import AuthLogFilters, AuthLogListSchema
from .use_cases.get_auth_logs import GetAuthLogsUseCaseProtocol

router = APIRouter(
    prefix='/api/auth',
    tags=['Auth Admin'],
    dependencies=[Depends(require_admin)],
)


@router.get('/admin/auth-logs', response_model=AuthLogListSchema)
async def get_auth_logs_admin(
    filters: AuthLogFilters = Depends(),
    use_case: GetAuthLogsUseCaseProtocol = Depends(get_auth_logs_use_case),
) -> AuthLogListSchema:
    return await use_case(filters)
