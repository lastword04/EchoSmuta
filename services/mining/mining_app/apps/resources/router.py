import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.captcha import CaptchaVerificationRequest

from ...core.db import Session
from ...core.depends import get_service_token_payload, get_user_token_payload
from .depends import (
    get_create_mining_action_use_case,
    get_get_mining_action_use_case,
    get_get_mining_status_use_case,
    get_get_my_resources_use_case,
    get_get_resource_by_slug_use_case,
    get_get_resources_for_character_use_case,
)
from .models import CharacterResource, CharacterResourceOperation, LocationResource, Resource
from .schemas import (
    CharacterResourceOperationRequest,
    CharacterResourceOperationResponse,
    CharacterResourcesResponse,
    LocationResourceReadSchema,
    LocationResourcesAndCharacterStats,
    MiningActionReadSchema,
    MiningActionResponseSchema,
    ResourceReadSchema,
    ResourseCharacterResponse,
)
from .use_cases.get_resources import GetResourcesForCharacterUseCaseProtocol
from .use_cases.mining.create import CreateMiningActionUseCaseProtocol
from .use_cases.mining.get import GetMiningActionUseCaseProtocol
from .use_cases.mining.get_status import GetMiningStatusUseCaseProtocol
from .use_cases.resources.get_by_slug import GetBySlugUseCaseProtocol
from .use_cases.resources.get_my_resources import GetMyUseCaseProtocol

router = APIRouter(prefix='/api/resources', tags=['Resources'])
internal_router = APIRouter(prefix='/internal/resources', tags=['Internal Resources'])


async def _change_character_resource(
    session: Session,
    character_id: uuid.UUID,
    resource_slug: str,
    data: CharacterResourceOperationRequest,
    operation_type: str
) -> CharacterResourceOperationResponse:
    existing_operation = await session.scalar(
        select(CharacterResourceOperation).where(CharacterResourceOperation.operation_id == data.operation_id)
    )
    if existing_operation is not None:
        return CharacterResourceOperationResponse(
            character_id=existing_operation.character_id,
            resource_slug=existing_operation.resource_slug,
            operation_id=existing_operation.operation_id,
            operation_type=existing_operation.operation_type,
            amount=existing_operation.amount,
            balance_after=existing_operation.balance_after
        )

    resource = await session.scalar(select(Resource).where(Resource.slug == resource_slug))
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Resource not found')

    character_resource = await session.scalar(
        select(CharacterResource)
        .where(
            CharacterResource.character_id == character_id,
            CharacterResource.resource_slug == resource_slug
        )
        .with_for_update()
    )
    if character_resource is None:
        if operation_type == 'debit':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Insufficient resources')

        character_resource = CharacterResource(
            character_id=character_id,
            resource_slug=resource_slug,
            amount=0
        )
        session.add(character_resource)
        await session.flush()

    if operation_type == 'debit':
        balance_after = character_resource.amount - data.amount
        if balance_after < 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Insufficient resources')
    else:
        balance_after = character_resource.amount + data.amount

    character_resource.amount = balance_after
    operation = CharacterResourceOperation(
        operation_id=data.operation_id,
        character_id=character_id,
        resource_slug=resource_slug,
        operation_type=operation_type,
        amount=data.amount,
        balance_after=balance_after
    )
    session.add(operation)
    await session.commit()

    return CharacterResourceOperationResponse(
        character_id=operation.character_id,
        resource_slug=operation.resource_slug,
        operation_id=operation.operation_id,
        operation_type=operation.operation_type,
        amount=operation.amount,
        balance_after=operation.balance_after
    )


@internal_router.post('/{resource_slug}/characters/{character_id}/debit', response_model=CharacterResourceOperationResponse)
async def debit_character_resource(
    data: CharacterResourceOperationRequest,
    session: Session,
    resource_slug: str = Path(...),
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterResourceOperationResponse:
    return await _change_character_resource(session, character_id, resource_slug, data, 'debit')


@internal_router.post('/{resource_slug}/characters/{character_id}/credit', response_model=CharacterResourceOperationResponse)
async def credit_character_resource(
    data: CharacterResourceOperationRequest,
    session: Session,
    resource_slug: str = Path(...),
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterResourceOperationResponse:
    return await _change_character_resource(session, character_id, resource_slug, data, 'credit')


@internal_router.get('/characters/{character_id}', response_model=CharacterResourcesResponse)
async def get_character_resources(
    session: Session,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterResourcesResponse:
    result = await session.execute(
        select(Resource.name, CharacterResource.resource_slug, CharacterResource.amount)
        .join(CharacterResource, CharacterResource.resource_slug == Resource.slug)
        .where(CharacterResource.character_id == character_id)
    )
    resources = [
        ResourseCharacterResponse(resource_name=name, resource_slug=slug, amount=amount)
        for name, slug, amount in result.all()
    ]
    return CharacterResourcesResponse(character_id=character_id, resources=resources)


@internal_router.get('/locations', response_model=list[LocationResourceReadSchema])
async def get_locations_resources(
    session: Session,
    token: dict = Depends(get_service_token_payload)
) -> list[LocationResourceReadSchema]:
    result = await session.scalars(select(LocationResource))
    return list(result.all())

@internal_router.get('/players', response_model=dict)
async def get_players_resources(
    session: Session,
    token: dict = Depends(get_service_token_payload)
) -> dict:
    result = await session.execute(
        select(
            CharacterResource.resource_slug,
            func.sum(CharacterResource.amount).label('total')
        ).group_by(CharacterResource.resource_slug)
    )
    rows = result.all()
    return {
        "resources": [
            {"resource_slug": row.resource_slug, "amount": str(row.total)}
            for row in rows
        ]
    }

@internal_router.get('/')
async def get_all_resources(
    session: Session,
    token: dict = Depends(get_service_token_payload)
) -> list[dict]:
    result = await session.execute(select(Resource))
    resources = result.scalars().all()
    return [
        {
            "slug": r.slug,
            "name": r.name,
            "weight": r.weight,
            "price": r.price,
            "serial_number": r.serial_number,
        }
        for r in resources
    ]

@router.get('/', response_model=LocationResourcesAndCharacterStats)
async def get_resources_for_character(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    location_slug: str | None = Query(default=None),
    use_case: GetResourcesForCharacterUseCaseProtocol = Depends(get_get_resources_for_character_use_case),
) -> LocationResourcesAndCharacterStats:
    return await use_case(user, location_slug)

@router.get('/my', response_model=list[ResourseCharacterResponse])
async def get_my_resources(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyUseCaseProtocol = Depends(get_get_my_resources_use_case)
) -> list[ResourseCharacterResponse]:
    return await use_case(user)

@router.get('/{resource_slug}', response_model=ResourceReadSchema)
async def get_resource_by_slug(
    resource_slug: str = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetBySlugUseCaseProtocol = Depends(get_get_resource_by_slug_use_case)
) -> ResourceReadSchema:
    return await use_case(resource_slug, user)

@router.post('/mining/actions', response_model=MiningActionReadSchema)
async def create_mining_action(
    captcha: CaptchaVerificationRequest,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateMiningActionUseCaseProtocol = Depends(get_create_mining_action_use_case)
) -> MiningActionReadSchema:
    return await use_case(user, captcha)

@router.get('/mining/actions/{action_id}', response_model=MiningActionReadSchema)
async def get_mining_action(
    action_id: uuid.UUID = Path(..., description="The ID of the mining action to retrieve"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMiningActionUseCaseProtocol = Depends(get_get_mining_action_use_case)
) -> MiningActionReadSchema:
    return await use_case(action_id, user)

@router.get('/mining/status', response_model=MiningActionResponseSchema)
async def get_mining_status(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMiningStatusUseCaseProtocol = Depends(get_get_mining_status_use_case)
) -> MiningActionResponseSchema:
    return await use_case(user)
