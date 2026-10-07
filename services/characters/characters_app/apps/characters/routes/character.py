"""CRUD, выборки и статусы персонажа."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import (
    CharacterCreateSchema, CharacterReadSchema, CharacterSimpleReadSchema,
    CharacterListIds, CharacterSimpleListReadSchema, CharacterMultCreateSchema,
    UserListids, PaginationCharacterSimpleInfoReadSchema, CharacterSimpleInfoListReadSchema,
    TirednessStat, CharacterMiningStats, CharacterItemsBalance,
    CharacterWeightBalance, WeightStat,
)
from ..schemas import CharacterCreationStatus, CharacterFullInfoSchema
from ..use_cases.character.create_character import CreateCharacterUseCaseProtocol
from ..use_cases.character.delete_character import DeleteCharacterUseCaseProtocol
from ..use_cases.character.get_by_name import GetByNameCharacterUseCaseProtocol
from ..use_cases.character.get_simple_character import GetSimpleCharacterUseCaseProtocol
from ..use_cases.character.get_all_by_user import GetCharactersByUserUseCaseProtocol
from ..use_cases.character.get_simple_ids_characters import GetSimpleByIdsCharactersUseCaseProtocol
from ..use_cases.character.get_simple_me import GetSimpleMeCharactersUseCaseProtocol
from ..use_cases.character.get_character import GetCharacterUseCaseProtocol
from ..use_cases.character.get_full_character_by_name import GetFullCharacterByNameUseCaseProtocol
from ..use_cases.character.create_mult_character import CreateCharacterMultUseCaseProtocol
from ..use_cases.character.check_create_character import CheckCreateCharacterStatusUseCaseProtocol
from ..use_cases.character.get_me import GetMeUseCaseProtocol
from ..use_cases.characters.simple_by_user_id import GetSimpleCharacterByUserUseCaseProtocol
from ..use_cases.characters.list_simple_by_users_ids import GetListSimpleCharactersByUsersIdsUseCaseProtocol
from ..use_cases.characters_chat.get_online_characters import GetOnlineCharactersUseCaseProtocol
from ..use_cases.characters_chat.get_by_ids import GetCharactersByIdsUseCaseProtocol
from ..use_cases.characters_chat.get import GetSimpleCharacterInfoUseCaseProtocol
from ..use_cases.characters.update_tiredness import UpdateCharacterTirednessUseCaseProtocol
from ..use_cases.characters.update_weight import UpdateCharacterWeightUseCaseProtocol
from ..use_cases.characters.mining.items.get_character_item_balance import GetCharacterItemBalanceUseCaseProtocol
from ..use_cases.characters.mining.weight.get_character_weight_balance import GetCharacterWeightBalanceUseCaseProtocol
from ....core.depends import get_service_token_payload, get_user_token_payload
from ..deps import (
    get_create_character_use_case,
    get_delete_character_use_case,
    get_get_by_name_character_use_case,
    get_simple_character_use_case,
    get_character_get_by_user_use_case,
    get_simple_by_ids_characters_use_case,
    get_simple_me_characters_use_case,
    get_create_character_mult_use_case,
    get_check_create_character_status_use_case,
    get_me_use_case,
    get_simple_character_by_user_use_case,
    get_list_simple_characters_by_users_use_case,
    get_get_online_characters_use_case,
    get_get_characters_by_ids_use_case,
    get_get_simple_character_info_use_case,
    get_get_full_character,
    get_get_full__character_by_name,
    get_update_tiredness_use_case,
    get_character_item_balance_use_case,
    get_character_weight_balance_use_case,
    get_character_update_weight_use_case,
)

router = APIRouter()


@router.get('/online', response_model=PaginationCharacterSimpleInfoReadSchema)
async def get_online_characters(
    limit: int = Query(10, gt=0, le=100, description="Number of slots to return"),
    offset: int = Query(0, ge=0, description="Number of slots to skip"),
    location_slug: Optional[str] = Query(None, description="Location where characters"),
    room_id: Optional[str] = Query(None, description="Virtual room (house:uuid, inn:inside)"),
    token: dict = Depends(get_service_token_payload),
    use_case: GetOnlineCharactersUseCaseProtocol = Depends(get_get_online_characters_use_case)
) -> PaginationCharacterSimpleInfoReadSchema:
    return await use_case(limit, offset, location_slug, room_id)


@router.get('/simple/me', response_model=CharacterSimpleReadSchema)
async def get_simple_me(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetSimpleMeCharactersUseCaseProtocol = Depends(get_simple_me_characters_use_case)
) -> CharacterSimpleReadSchema:
    return await use_case(token)

@router.post('/simple/ids', response_model=CharacterSimpleListReadSchema)
async def get_simple_by_ids(
    ids: CharacterListIds,
    token: dict = Depends(get_service_token_payload),
    use_case: GetSimpleByIdsCharactersUseCaseProtocol = Depends(get_simple_by_ids_characters_use_case)
) -> CharacterSimpleListReadSchema:
    return await use_case(ids.ids)

@router.get('/simple/info/{character_id}', response_model=CharacterMiningStats)
async def get_simple_character_info(
    character_id: uuid.UUID = Path(..., description="Id of character"),
    token: dict = Depends(get_service_token_payload),
    use_case: GetSimpleCharacterInfoUseCaseProtocol = Depends(get_get_simple_character_info_use_case)
) -> CharacterMiningStats:
    return await use_case(character_id)

@router.post('/simple/info/ids', response_model=CharacterSimpleInfoListReadSchema)
async def get_simple_character_info_by_ids(
    ids: CharacterListIds,
    is_online: Optional[bool] = Query(None, description="Search only online or offline characters"),
    token: dict = Depends(get_service_token_payload),
    use_case: GetCharactersByIdsUseCaseProtocol = Depends(get_get_characters_by_ids_use_case)
) -> CharacterSimpleInfoListReadSchema:
    return await use_case(ids, is_online)

@router.post('/register', response_model=CharacterReadSchema, status_code=201)
async def create_default_character(character: CharacterCreateSchema,
                           token: dict = Depends(get_service_token_payload),
                           use_case: CreateCharacterUseCaseProtocol = Depends(get_create_character_use_case)) -> CharacterReadSchema:
    result = await use_case(character)
    return result

@router.get('/users/character-creation-status', response_model=CharacterCreationStatus)
async def check_character_creation_status(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CheckCreateCharacterStatusUseCaseProtocol = Depends(get_check_create_character_status_use_case)
) -> CharacterCreationStatus:
    return await use_case(token)


@router.get('/me', response_model=list[CharacterReadSchema])
async def get_me(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCharactersByUserUseCaseProtocol = Depends(get_character_get_by_user_use_case)
) -> list[CharacterReadSchema]:
    return await use_case(token)

@router.get('/only-me', response_model=CharacterReadSchema)
async def get_only_me(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMeUseCaseProtocol = Depends(get_me_use_case)
) -> CharacterReadSchema:
    return await use_case(token)

@router.post('/', response_model=CharacterReadSchema, status_code=201)
async def create_character(character: CharacterMultCreateSchema,
                           token: UserTokenDataReadSchema = Depends(get_user_token_payload),
                           use_case: CreateCharacterMultUseCaseProtocol = Depends(get_create_character_mult_use_case)
                           ) -> CharacterReadSchema:
    result = await use_case(character, token)
    return result

@router.delete('/{character_id}', response_model=None, status_code=204)
async def delete_character(character_id: uuid.UUID = Path(...),
                           token: dict = Depends(get_service_token_payload),
                           use_case: DeleteCharacterUseCaseProtocol = Depends(get_delete_character_use_case)
                           ) -> None:
    await use_case(character_id)
    return None

@router.get('/name/{name}/info', response_model=CharacterFullInfoSchema)
async def get_full_character_by_name(name: str = Path(..., title="Character Name", description="The name of the character to retrieve"),
                           use_case: GetFullCharacterByNameUseCaseProtocol = Depends(get_get_full__character_by_name)) -> CharacterFullInfoSchema:
    return await use_case(name)

@router.get('/name/{name}/simple', response_model=CharacterSimpleReadSchema)
async def get_character_by_name(name: str = Path(..., title="Character Name", description="The name of the character to retrieve"),
                           token: UserTokenDataReadSchema = Depends(get_user_token_payload),
                           use_case: GetByNameCharacterUseCaseProtocol = Depends(get_get_by_name_character_use_case)) -> CharacterReadSchema:
    return await use_case(name)

@router.get('/name/{name}', response_model=CharacterSimpleReadSchema)
async def get_character_by_name_service(name: str = Path(..., title="Character Name", description="The name of the character to retrieve"),
                           token: dict = Depends(get_service_token_payload),
                           use_case: GetByNameCharacterUseCaseProtocol = Depends(get_get_by_name_character_use_case)) -> CharacterReadSchema:
    return await use_case(name)



@router.post('/simple/users/', response_model=CharacterSimpleListReadSchema)
async def get_list_simple_characters_by_users(users: UserListids,
                           token: dict = Depends(get_service_token_payload),
                           use_case: GetListSimpleCharactersByUsersIdsUseCaseProtocol = Depends(get_list_simple_characters_by_users_use_case)
                           ) -> CharacterSimpleReadSchema:
    return await use_case(users)

@router.get('/simple/user/{user_id}', response_model=CharacterSimpleReadSchema)
async def get_simple_character_by_user(user_id: uuid.UUID = Path(...),
                           token: dict = Depends(get_service_token_payload),
                           use_case: GetSimpleCharacterByUserUseCaseProtocol = Depends(get_simple_character_by_user_use_case)
                           ) -> CharacterSimpleReadSchema:
    return await use_case(user_id)

@router.get('/simple/{character_id}', response_model=CharacterSimpleReadSchema)
async def get_simple_character(character_id: uuid.UUID = Path(...),
                           token: dict = Depends(get_service_token_payload),
                           use_case: GetSimpleCharacterUseCaseProtocol = Depends(get_simple_character_use_case)) -> CharacterSimpleReadSchema:
    return await use_case(character_id)

@router.get('/simple/{character_id}/balance', response_model=CharacterItemsBalance)
async def get_character_item_balance(character_id: uuid.UUID = Path(...),
                                    token: dict = Depends(get_service_token_payload),
                                    use_case: GetCharacterItemBalanceUseCaseProtocol = Depends(get_character_item_balance_use_case)
                                     ) -> CharacterItemsBalance:
    return await use_case(character_id)

@router.get('/simple/{character_id}/weight', response_model=CharacterWeightBalance)
async def get_character_weight_balance(character_id: uuid.UUID = Path(...),
                                       token: dict = Depends(get_service_token_payload),
                                       use_case: GetCharacterWeightBalanceUseCaseProtocol = Depends(get_character_weight_balance_use_case)
                                        ) -> CharacterWeightBalance:
    return await use_case(character_id)

@router.get('/{character_id}', response_model=CharacterFullInfoSchema)
async def get_character(
    character_id: uuid.UUID = Path(..., description="Id of character"),
    use_case: GetCharacterUseCaseProtocol = Depends(get_get_full_character)
) -> CharacterFullInfoSchema:
    return await use_case(character_id)

@router.put('/{character_id}/tiredness', response_model=StatusOkSchema)
async def update_tiredness(
    stats: TirednessStat,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: UpdateCharacterTirednessUseCaseProtocol = Depends(get_update_tiredness_use_case)
) -> StatusOkSchema:
    return await use_case(character_id, stats)

@router.put('/{character_id}/weight', response_model=StatusOkSchema)
async def update_weight(
    stats: WeightStat,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: UpdateCharacterWeightUseCaseProtocol = Depends(get_character_update_weight_use_case)
) -> StatusOkSchema:
    return await use_case(character_id, stats)
