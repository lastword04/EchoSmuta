from typing_extensions import Self
from shared.schemas.characters import CharacterSimpleListReadSchema, UserListids
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 


class GetListSimpleCharactersByUsersIdsUseCaseProtocol(UseCaseProtocol[CharacterSimpleListReadSchema]):
    async def __call__(self: Self, users: UserListids) -> CharacterSimpleListReadSchema:
        ...


class GetListSimpleCharactersByUsersIdsUseCase(GetListSimpleCharactersByUsersIdsUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, users: UserListids) -> CharacterSimpleListReadSchema:
        return  await self.service.get_simple_main_by_user_ids(users.ids)

