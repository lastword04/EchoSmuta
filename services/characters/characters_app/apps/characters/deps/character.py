from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ...stats.depends import get_stats_publisher
from ...stats.services.effective_stats import EffectiveStatsService
from ...stats.services.publisher.stats_publisher import StatsPublisher
from ..adapters.category import CategoryServiceClientProtocol
from ..adapters.chats import ChatSettingsServiceClientProtocol
from ..adapters.files import FileServiceClientProtocol
from ..adapters.notebook import CreateNotebookAdapter
from ..adapters.panels import CreateItemsAdapterProtocol
from ..events.publisher import RedisPublisherProtocol
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..services.character.characters import (
    CharacterServiceProtocol,
    CharacterService,
    CharacterCreateCheckerProtocol,
    CharacterCreateChecker,
    UpdateCharacterTirednessServiceProtocol,
    UpdateCharacterTirednessService,
    GetFullInfoCharacterServiceProtocol,
    GetFullInfoCharacterService,
    UpdateCharacterProtocol,
    UpdateCharacterService,
    UpdateCharacterStatusServiceProtocol,
    UpdateCharacterStatusService,
    GetMainCharacterByUserIdProtocol,
    GetMainCharacterByUserIdService,
)
from ..services.info.characters_info import CharacterInfoServiceProtocol
from ..services.referrals.referral_link import ReferralLinkServiceProtocol
from ..services.settings.experience_settings import GlobalCharacterExperienceSettingsServiceProtocol
from ..services.settings.global_settings import GlobalCharacterSettingsServiceProtocol
from ..services.settings.race_settings import RaceSettingsServiceProtocol
from ..services.settings.user_character_settings import UserCharacterSettingsServiceProtocol
from ..services.skills.applied_character_history import AppliedCharacterHistoryServiceProtocol
from ..services.skills.character_ability_skills import CharacterAbilitySkillsServiceProtocol
from ..services.skills.character_distributions import CharacterDistributionsServiceProtocol
from ...rest.services.house_guest_service import HouseGuestServiceProtocol
from ...rest.depends import get_house_guest_service
from ..use_cases.character.check_create_character import (
    CheckCreateCharacterStatusUseCaseProtocol,
    CheckCreateCharacterStatusUseCase,
)
from ..use_cases.character.create_character import (
    CreateCharacterUseCaseProtocol,
    CreateCharacterUseCase,
)
from ..use_cases.character.create_mult_character import (
    CreateCharacterMultUseCaseProtocol,
    CreateCharacterMultUseCase,
)
from ..use_cases.character.delete_character import (
    DeleteCharacterUseCaseProtocol,
    DeleteCharacterUseCase,
)
from ..use_cases.character.get_by_name import (
    GetByNameCharacterUseCaseProtocol,
    GetByNameCharacterUseCase,
)
from ..use_cases.character.get_character import (
    GetCharacterUseCaseProtocol,
    GetCharacterUseCase,
)
from ..use_cases.character.get_all_by_user import (
    GetCharactersByUserUseCaseProtocol,
    GetCharactersByUserUseCase,
)
from ..use_cases.character.get_full_character_by_name import (
    GetFullCharacterByNameUseCaseProtocol,
    GetFullCharacterByNameUseCase,
)
from ..use_cases.character.get_me import (
    GetMeUseCaseProtocol,
    GetMeUseCase,
)
from ..use_cases.character.get_simple_character import (
    GetSimpleCharacterUseCaseProtocol,
    GetSimpleCharacterUseCase,
)
from ..use_cases.character.get_simple_ids_characters import (
    GetSimpleByIdsCharactersUseCaseProtocol,
    GetSimpleByIdsCharactersUseCase,
)
from ..use_cases.character.get_simple_me import (
    GetSimpleMeCharactersUseCaseProtocol,
    GetSimpleMeCharactersUseCase,
)
from ..use_cases.characters.list_simple_by_users_ids import (
    GetListSimpleCharactersByUsersIdsUseCaseProtocol,
    GetListSimpleCharactersByUsersIdsUseCase,
)
from ..use_cases.characters.simple_by_user_id import (
    GetSimpleCharacterByUserUseCaseProtocol,
    GetSimpleCharacterByUserUseCase,
)
from ..use_cases.characters.update_tiredness import (
    UpdateCharacterTirednessUseCaseProtocol,
    UpdateCharacterTirednessUseCase,
)
from ..use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol
from ..use_cases.skills.add_stats_by_ability_skills import (
    AddStatsToCharacterUseCaseProtocol,
    AddStatsToCharacterUseCase,
)
from ..use_cases.skills.update_stats_by_ability_skills import (
    UpdateStatsToCharacterUseCaseProtocol,
    UpdateStatsToCharacterUseCase,
)
from ..use_cases.skills.calculate_stats_for_ability_skills import (
    CalculateStatsForChangeUseCaseProtocol,
    CalculateStatsForChangeUseCase,
)
from ..use_cases.referrals.get_referral_link import (
    GetReferralLinkUseCaseProtocol,
    GetReferralLinkUseCase,
)
from .adapters import (
    get_file_client,
    get_notebook_adapter,
    get_items_adapter,
    get_chat_settings_client,
    get_category_stats_adapter,
    get_redis_publisher,
    get_effective_stats_service,
)
from .info import get_character_info_service as get_characters_info_service
from .referrals import get_referral_link_service_dep
from .settings import (
    get_global_character_settings_service_dep,
    get_global_character_experience_settings_service,
    get_race_settings_service_dep,
    get_user_character_settings_service_dep,
)
from .skills import (
    get_character_ability_skills_service,
    get_applied_character_history_service,
    get_character_distributions_service,
)
from .valid import __get_character_repository, get_get_online_status_or_raise_use_case


def get_character_create_checker_dep(repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
                                    user_character_settings_service: UserCharacterSettingsServiceProtocol = Depends(get_user_character_settings_service_dep),
                                    global_settings_service: GlobalCharacterSettingsServiceProtocol = Depends(get_global_character_settings_service_dep)) -> CharacterCreateCheckerProtocol:
    return CharacterCreateChecker(repository=repository, user_character_settings_service=user_character_settings_service, global_settings_service=global_settings_service)


def get_check_create_character_status_use_case(service: CharacterCreateCheckerProtocol = Depends(get_character_create_checker_dep)) -> CheckCreateCharacterStatusUseCaseProtocol:
    return CheckCreateCharacterStatusUseCase(service=service)


def get_character_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
                          global_settings_service: GlobalCharacterSettingsServiceProtocol = Depends(get_global_character_settings_service_dep),
                          experience_settings_service: GlobalCharacterExperienceSettingsServiceProtocol = Depends(get_global_character_experience_settings_service),
                          character_ability_skills_service: CharacterAbilitySkillsServiceProtocol = Depends(get_character_ability_skills_service),
                          applied_character_history_service: AppliedCharacterHistoryServiceProtocol = Depends(get_applied_character_history_service),
                          race_settings_service: RaceSettingsServiceProtocol = Depends(get_race_settings_service_dep),
                          client: FileServiceClientProtocol = Depends(get_file_client),
                          user_character_settings: UserCharacterSettingsServiceProtocol = Depends(get_user_character_settings_service_dep),
                          creation_checker: CharacterCreateCheckerProtocol = Depends(get_character_create_checker_dep),
                          referral_link_service: ReferralLinkServiceProtocol = Depends(get_referral_link_service_dep),
                          notebook_adapter: CreateNotebookAdapter = Depends(get_notebook_adapter),
                          items_adapter: CreateItemsAdapterProtocol = Depends(get_items_adapter),
                          chat_settings_service: ChatSettingsServiceClientProtocol = Depends(get_chat_settings_client),
                          characters_info: CharacterInfoServiceProtocol = Depends(get_characters_info_service),
                          character_distributions_service: CharacterDistributionsServiceProtocol = Depends(get_character_distributions_service)
                          ) -> CharacterServiceProtocol:
    """
    Функция для получения сервиса персонажей.
    """
    return CharacterService(repository=repository,
                            global_settings_service=global_settings_service,
                            experience_settings_service=experience_settings_service,
                            ability_skills_service=character_ability_skills_service,
                            applied_character_history_service=applied_character_history_service,
                            race_settings_service=race_settings_service,
                            file_client=client,
                            user_character_settings_service=user_character_settings,
                            character_checker=creation_checker,
                            referral_link_service=referral_link_service,
                            notebook_adapter=notebook_adapter,
                            items_adapter=items_adapter,
                            chat_settings_service=chat_settings_service,
                            characters_info=characters_info,
                            character_distributions_service=character_distributions_service
                            )


def get_character_update_tiredness_service(
    repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
    publisher: StatsPublisher = Depends(get_stats_publisher),
) -> UpdateCharacterTirednessServiceProtocol:
    return UpdateCharacterTirednessService(repository=repository, publisher=publisher)


def get_update_tiredness_use_case(service: UpdateCharacterTirednessServiceProtocol = Depends(get_character_update_tiredness_service)) -> UpdateCharacterTirednessUseCaseProtocol:
    return UpdateCharacterTirednessUseCase(service)


def get_character_info_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
                               characters_info: CharacterInfoServiceProtocol = Depends(get_characters_info_service),
                               category_adapter: CategoryServiceClientProtocol = Depends(get_category_stats_adapter)) -> GetFullInfoCharacterServiceProtocol:
    return GetFullInfoCharacterService(repository=repository, characters_info=characters_info, category_service=category_adapter)


def get_get_full_character(service: GetFullInfoCharacterServiceProtocol = Depends(get_character_info_service)) -> GetCharacterUseCaseProtocol:
    return GetCharacterUseCase(service)


def get_get_full__character_by_name(service: GetFullInfoCharacterServiceProtocol = Depends(get_character_info_service)) -> GetFullCharacterByNameUseCaseProtocol:
    return GetFullCharacterByNameUseCase(service)


def get_create_character_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> CreateCharacterUseCaseProtocol:
    return CreateCharacterUseCase(service=service)


def get_update_character_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository)) -> UpdateCharacterProtocol:
    return UpdateCharacterService(repository=repository)


def get_delete_character_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> DeleteCharacterUseCaseProtocol:
    return DeleteCharacterUseCase(service=service)


def get_get_by_name_character_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> GetByNameCharacterUseCaseProtocol:
    return GetByNameCharacterUseCase(service=service)


def get_simple_character_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> GetSimpleCharacterUseCaseProtocol:
    return GetSimpleCharacterUseCase(service=service)


def get_simple_me_characters_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> GetSimpleMeCharactersUseCaseProtocol:
    return GetSimpleMeCharactersUseCase(service=service)


def get_character_get_by_user_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> GetCharactersByUserUseCaseProtocol:
    return GetCharactersByUserUseCase(service)


def get_simple_by_ids_characters_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> GetSimpleByIdsCharactersUseCaseProtocol:
    return GetSimpleByIdsCharactersUseCase(service=service)


def get_create_character_mult_use_case(service: CharacterServiceProtocol = Depends(get_character_service)) -> CreateCharacterMultUseCaseProtocol:
    return CreateCharacterMultUseCase(service=service)


def get_update_character_status_service(
    repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
    publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
    house_guest_service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
) -> UpdateCharacterStatusServiceProtocol:
    return UpdateCharacterStatusService(
        repository=repository,
        publisher=publisher,
        house_guest_service=house_guest_service,
    )


def get_main_character_by_user_id_service(character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository)
                                           ) -> GetMainCharacterByUserIdProtocol:
    return GetMainCharacterByUserIdService(repository=character_repository)


def get_me_use_case(
    character_service: CharacterServiceProtocol = Depends(get_character_service),
    valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol = Depends(get_get_online_status_or_raise_use_case),
    effective_stats: EffectiveStatsService = Depends(get_effective_stats_service),
) -> GetMeUseCaseProtocol:
    return GetMeUseCase(
        service=character_service,
        valid_or_raise=valid_or_raise,
        effective_stats=effective_stats,
    )


def get_simple_character_by_user_use_case(character_service: CharacterServiceProtocol = Depends(get_character_service)) -> GetSimpleCharacterByUserUseCaseProtocol:
    return GetSimpleCharacterByUserUseCase(service=character_service)


def get_list_simple_characters_by_users_use_case(character_service: CharacterServiceProtocol = Depends(get_character_service)) -> GetListSimpleCharactersByUsersIdsUseCaseProtocol:
    return GetListSimpleCharactersByUsersIdsUseCase(service=character_service)


def get_add_stats_by_ability_skills_use_case(service: CharacterServiceProtocol = Depends(get_character_service)
) -> AddStatsToCharacterUseCaseProtocol:
    return AddStatsToCharacterUseCase(service=service)


def get_update_stats_by_ability_skills_use_case(service: CharacterServiceProtocol = Depends(get_character_service)
) -> UpdateStatsToCharacterUseCaseProtocol:
    return UpdateStatsToCharacterUseCase(service=service)


def get_calculate_character_stats_use_case(service: CharacterServiceProtocol = Depends(get_character_service)
) -> CalculateStatsForChangeUseCaseProtocol:
    return CalculateStatsForChangeUseCase(service=service)


def get_referral_link_use_case_dep(service: ReferralLinkServiceProtocol = Depends(get_referral_link_service_dep),
                                   character_service: CharacterServiceProtocol = Depends(get_character_service)) -> GetReferralLinkUseCaseProtocol:
    return GetReferralLinkUseCase(service=service, character_service=character_service)


