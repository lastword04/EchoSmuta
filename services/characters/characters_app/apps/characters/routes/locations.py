"""Локации и распределение персонажей по ним."""
from fastapi import APIRouter, Depends, Path
from sqlalchemy import select

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterReadSchema, CharacterIdsResponse
from shared.schemas.locations import LocationReadSchema

from ....core.db import Session
from ....core.depends import get_service_token_payload, get_user_token_payload
from ..models import Character, Location
from ..schemas import LocationCharacterCountSchema
from ..use_cases.locations.count_characters_by_locations import CountCharactersByLocationUseCaseProtocol
from ..use_cases.locations.get_by_slug import GetLocationBySlugUseCaseProtocol
from ..use_cases.locations.change_location import ChangeCharacterLocationUseCaseProtocol
from ..deps import (
    get_count_characters_by_location_use_case,
    get_location_by_slug_use_case,
    get_change_character_location_use_case,
)

router = APIRouter()


@router.get('/locations/count', response_model=list[LocationCharacterCountSchema])
async def count_characters_by_location(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CountCharactersByLocationUseCaseProtocol = Depends(get_count_characters_by_location_use_case)
) -> list[LocationCharacterCountSchema]:
    return await use_case(token)

@router.get('/locations/{slug}', response_model=LocationReadSchema)
async def get_location_by_slug(
    slug: str = Path(..., title="Location Slug", description="The slug of the location to retrieve"),
    token: dict = Depends(get_service_token_payload),
    use_case: GetLocationBySlugUseCaseProtocol = Depends(get_location_by_slug_use_case)
) -> LocationReadSchema:
    return await use_case(slug)

@router.post('/locations/{slug}', response_model=CharacterReadSchema)
async def change_character_location(
    slug: str = Path(..., title="Location Slug", description="The slug of the location to change to"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ChangeCharacterLocationUseCaseProtocol = Depends(get_change_character_location_use_case)
) -> CharacterReadSchema:
    return await use_case(location_slug=slug, user=token)

@router.get('/by-location/{location_slug}', response_model=CharacterIdsResponse)
async def get_character_ids_by_location(
        session: Session,
        location_slug: str = Path(..., description="Location slug"),
        token: dict = Depends(get_service_token_payload),
    ) -> CharacterIdsResponse:
        """ID всех персонажей, находящихся в одном городе с указанной локацией"""
        location = await session.scalar(
            select(Location).where(Location.slug == location_slug)
        )
        if location is None:
            return CharacterIdsResponse(ids=[])

        stmt = (
            select(Character.id)
            .join(Location, Character.location_slug == Location.slug)
            .where(Location.city_id == location.city_id)
            .where(Character.is_active.is_(True))
        )
        result = await session.execute(stmt)
        return CharacterIdsResponse(ids=[row[0] for row in result.all()])
