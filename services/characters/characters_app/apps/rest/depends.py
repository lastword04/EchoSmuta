from fastapi import Depends
from shared.services.templates import TextTemplateService
from ...core.redis import get_redis_client
from ...core.db import AsyncSession, get_async_session
from ..characters.repositories.character.characters import CharacterRepository, CharacterRepositoryProtocol
from ..characters.adapters.mining import MiningServiceClient, MiningServiceClientProtocol
from ..stats.depends import get_stats_publisher
from ..stats.repositories.buff_repository import BuffRepository
from ..stats.services.publisher.stats_publisher import StatsPublisher
from ..stats.services.collector.buffs import BuffsCollector
from ..stats.services.collector.equipment import EquipmentCollector
from ..stats.services.collector.modifiers import ModifiersCollector

from .repositories.inn_repository import RestRepository, RestRepositoryProtocol
from .repositories.house_repository import HouseRepository, HouseRepositoryProtocol
from .repositories.house_furniture_repository import HouseFurnitureRepository, HouseFurnitureRepositoryProtocol
from .repositories.house_guest_request_repository import HouseGuestRequestRepository, HouseGuestRequestRepositoryProtocol
from .repositories.house_guest_session_repository import HouseGuestSessionRepository, HouseGuestSessionRepositoryProtocol
from .repositories.inventory_item_work_accumulator_repository import InventoryItemWorkAccumulatorRepository
from .services.rest_service import RestService, RestServiceProtocol
from .services.rest_templates import RestTemplateService
from .services.house_service import HouseService, HouseServiceProtocol
from .services.house_guest_service import HouseGuestService, HouseGuestServiceProtocol
from .use_cases.rent_room import RentRoomUseCase, RentRoomUseCaseProtocol
from .use_cases.exit_room import ExitRoomUseCase, ExitRoomUseCaseProtocol
from .use_cases.enter_room import EnterRoomUseCase, EnterRoomUseCaseProtocol
from .use_cases.get_status import GetRestStatusUseCase, GetRestStatusUseCaseProtocol
from .use_cases.expire_rentals import ExpireRestRentalsUseCase, ExpireRestRentalsUseCaseProtocol
from .use_cases.sync_expiry import SyncExpiryUseCase, SyncExpiryUseCaseProtocol
from .use_cases.buy_house import BuyHouseUseCase, BuyHouseUseCaseProtocol
from .use_cases.enter_house import EnterHouseUseCase, EnterHouseUseCaseProtocol
from .use_cases.exit_house import ExitHouseUseCase, ExitHouseUseCaseProtocol
from .use_cases.get_house_status import GetHouseStatusUseCase, GetHouseStatusUseCaseProtocol
from .use_cases.install_furniture import InstallFurnitureUseCase, InstallFurnitureUseCaseProtocol
from .use_cases.uninstall_furniture import UninstallFurnitureUseCase, UninstallFurnitureUseCaseProtocol
from .use_cases.get_house_furniture import GetHouseFurnitureUseCase, GetHouseFurnitureUseCaseProtocol
from .use_cases.get_my_furniture import GetMyFurnitureUseCase, GetMyFurnitureUseCaseProtocol
from .use_cases.update_house_wallpaper import UpdateHouseWallpaperUseCase, UpdateHouseWallpaperUseCaseProtocol
from .use_cases.knock_house import KnockHouseUseCase, KnockHouseUseCaseProtocol
from .use_cases.accept_guest_request import AcceptGuestRequestUseCase, AcceptGuestRequestUseCaseProtocol
from .use_cases.reject_guest_request import RejectGuestRequestUseCase, RejectGuestRequestUseCaseProtocol
from .use_cases.kick_house_guest import KickHouseGuestUseCase, KickHouseGuestUseCaseProtocol
from .use_cases.get_house_guests import GetHouseGuestsUseCase, GetHouseGuestsUseCaseProtocol
from .use_cases.expire_house_requests import ExpireHouseRequestsUseCase, ExpireHouseRequestsUseCaseProtocol
from .use_cases.wear_house_furniture import WearHouseFurnitureUseCase, WearHouseFurnitureUseCaseProtocol
from .events.publisher import RedisPublisher
from .events.rest_events import RestEvents
from .events.house_events import HouseEvents
from ..characters.events.change_location import ChangeLocationEvents, ChangeLocationEventsProtocol
from ...settings import get_settings, Settings, settings


# Singleton template service
_text_template_instance: TextTemplateService | None = None


def get_text_template_service() -> TextTemplateService:
    global _text_template_instance
    if _text_template_instance is None:
        _text_template_instance = TextTemplateService(settings.system_messages_file_path)
    return _text_template_instance


def get_redis_publisher() -> RedisPublisher:
    return RedisPublisher(get_redis_client())


def get_rest_events() -> RestEvents:
    return RestEvents(get_redis_publisher())


def get_rest_template_service() -> RestTemplateService:
    return RestTemplateService(get_text_template_service())


def get_house_events() -> HouseEvents:
    return HouseEvents(get_redis_publisher())


def get_mining_adapter(settings: Settings = Depends(get_settings)) -> MiningServiceClientProtocol:
    """Локальная версия: импорт из characters.deps создавал циклический импорт."""
    return MiningServiceClient(base_url=settings.mining_service_app.base_url)

def get_change_location_events(
    publisher: RedisPublisher = Depends(get_redis_publisher),
) -> ChangeLocationEventsProtocol:
    return ChangeLocationEvents(publisher)



# Репозитории
def __get_rest_repository(
    session: AsyncSession = Depends(get_async_session),
) -> RestRepositoryProtocol:
    return RestRepository(session=session)


def __get_character_repository(
    session: AsyncSession = Depends(get_async_session),
) -> CharacterRepositoryProtocol:
    return CharacterRepository(session=session)


def __get_house_repository(
    session: AsyncSession = Depends(get_async_session),
) -> HouseRepositoryProtocol:
    return HouseRepository(session=session)


def __get_house_furniture_repository(
    session: AsyncSession = Depends(get_async_session),
) -> HouseFurnitureRepositoryProtocol:
    return HouseFurnitureRepository(session=session)


def __get_house_guest_request_repository(
    session: AsyncSession = Depends(get_async_session),
) -> HouseGuestRequestRepositoryProtocol:
    return HouseGuestRequestRepository(session=session)


def __get_house_guest_session_repository(
    session: AsyncSession = Depends(get_async_session),
) -> HouseGuestSessionRepositoryProtocol:
    return HouseGuestSessionRepository(session=session)


# Сервис
def get_rest_service(
    rest_repo: RestRepositoryProtocol = Depends(__get_rest_repository),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
    publisher: StatsPublisher = Depends(get_stats_publisher),
    settings: Settings = Depends(get_settings),
    events: RestEvents = Depends(get_rest_events),
    template_service: RestTemplateService = Depends(get_rest_template_service),
    change_location_events: ChangeLocationEventsProtocol = Depends(get_change_location_events),
) -> RestServiceProtocol:
    return RestService(
        rest_repository=rest_repo,
        character_repository=char_repo,
        publisher=publisher,
        settings=settings,
        events=events,
        template_service=template_service,
        change_location_events=change_location_events,
    )

def get_house_service(
    house_repo: HouseRepositoryProtocol = Depends(__get_house_repository),
    furniture_repo: HouseFurnitureRepositoryProtocol = Depends(__get_house_furniture_repository),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
    publisher: StatsPublisher = Depends(get_stats_publisher),
    settings: Settings = Depends(get_settings),
    mining_client: MiningServiceClientProtocol = Depends(get_mining_adapter),
    guest_session_repo: HouseGuestSessionRepositoryProtocol = Depends(__get_house_guest_session_repository),
    guest_request_repo: HouseGuestRequestRepositoryProtocol = Depends(__get_house_guest_request_repository),
    house_events: HouseEvents = Depends(get_house_events),
    events: RestEvents = Depends(get_rest_events),
    template_service: RestTemplateService = Depends(get_rest_template_service),
    change_location_events: ChangeLocationEventsProtocol = Depends(get_change_location_events),
) -> HouseServiceProtocol:
    return HouseService(
        house_repository=house_repo,
        character_repository=char_repo,
        publisher=publisher,
        settings=settings,
        mining_client=mining_client,
        furniture_repository=furniture_repo,
        guest_session_repository=guest_session_repo,
        guest_request_repository=guest_request_repo,
        house_events=house_events,
        events=events,
        template_service=template_service,
        change_location_events=change_location_events,
    )

def get_house_guest_service(
    house_repo: HouseRepositoryProtocol = Depends(__get_house_repository),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
    guest_request_repo: HouseGuestRequestRepositoryProtocol = Depends(__get_house_guest_request_repository),
    guest_session_repo: HouseGuestSessionRepositoryProtocol = Depends(__get_house_guest_session_repository),
    furniture_repo: HouseFurnitureRepositoryProtocol = Depends(__get_house_furniture_repository),
    mining_client: MiningServiceClientProtocol = Depends(get_mining_adapter),
    publisher: StatsPublisher = Depends(get_stats_publisher),
    settings: Settings = Depends(get_settings),
    events: RestEvents = Depends(get_rest_events),
    template_service: RestTemplateService = Depends(get_rest_template_service),
    house_events: HouseEvents = Depends(get_house_events),
    change_location_events: ChangeLocationEventsProtocol = Depends(get_change_location_events),
) -> HouseGuestServiceProtocol:
    return HouseGuestService(
        house_repository=house_repo,
        character_repository=char_repo,
        guest_request_repository=guest_request_repo,
        guest_session_repository=guest_session_repo,
        furniture_repository=furniture_repo,
        mining_client=mining_client,
        publisher=publisher,
        settings=settings,
        events=events,
        template_service=template_service,
        house_events=house_events,
        change_location_events=change_location_events,
    )


# Use Cases
def get_rent_room_use_case(
    service: RestServiceProtocol = Depends(get_rest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> RentRoomUseCaseProtocol:
    return RentRoomUseCase(service=service, character_repository=char_repo)


def get_exit_room_use_case(
    service: RestServiceProtocol = Depends(get_rest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> ExitRoomUseCaseProtocol:
    return ExitRoomUseCase(service=service, character_repository=char_repo)


def get_enter_room_use_case(
    service: RestServiceProtocol = Depends(get_rest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> EnterRoomUseCaseProtocol:
    return EnterRoomUseCase(service=service, character_repository=char_repo)


def get_rest_status_use_case(
    service: RestServiceProtocol = Depends(get_rest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> GetRestStatusUseCaseProtocol:
    return GetRestStatusUseCase(service=service, character_repository=char_repo)


def get_expire_rentals_use_case(
    service: RestServiceProtocol = Depends(get_rest_service),
) -> ExpireRestRentalsUseCaseProtocol:
    return ExpireRestRentalsUseCase(service=service)


def get_expire_rentals_use_case_factory(
    session: AsyncSession,
    redis_client
) -> ExpireRestRentalsUseCaseProtocol:
    """Factory для Celery tasks"""
    from ..characters.repositories.character.characters import CharacterRepository
    from ..stats.depends import get_stats_publisher
    
    rest_repo = RestRepository(session=session)
    char_repo = CharacterRepository(session=session)
    
    # Создаём publisher через фабрику stats
    from ..stats.services.publisher.stats_publisher import StatsPublisher
    from ..stats.services.collector.buffs import BuffsCollector
    from ..stats.services.collector.equipment import EquipmentCollector
    from ..stats.services.collector.modifiers import ModifiersCollector
    from ..stats.repositories.buff_repository import BuffRepository
    
    collector = BuffsCollector(buff_repository=BuffRepository(session=session))
    modifiers_collector = ModifiersCollector(
        collectors=[EquipmentCollector(), collector]
    )
    publisher = StatsPublisher(
        redis_client=redis_client,
        character_repository=char_repo,
        modifiers_collector=modifiers_collector,
        buffs_collector=collector,
    )
    
    service = RestService(
        rest_repository=rest_repo,
        character_repository=char_repo,
        publisher=publisher,
        settings=settings,
        events=RestEvents(RedisPublisher(redis_client)),
        template_service=RestTemplateService(get_text_template_service()),
        change_location_events=ChangeLocationEvents(RedisPublisher(redis_client)),
    )
    
    return ExpireRestRentalsUseCase(service=service)


def get_sync_expiry_use_case(
    service: RestServiceProtocol = Depends(get_rest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> SyncExpiryUseCaseProtocol:
    return SyncExpiryUseCase(service=service, character_repository=char_repo)


def get_buy_house_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> BuyHouseUseCaseProtocol:
    return BuyHouseUseCase(service=service, character_repository=char_repo)


def get_enter_house_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> EnterHouseUseCaseProtocol:
    return EnterHouseUseCase(service=service, character_repository=char_repo)


def get_exit_house_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> ExitHouseUseCaseProtocol:
    return ExitHouseUseCase(service=service, character_repository=char_repo)


def get_house_status_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> GetHouseStatusUseCaseProtocol:
    return GetHouseStatusUseCase(service=service, character_repository=char_repo)

def get_install_furniture_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> InstallFurnitureUseCaseProtocol:
    return InstallFurnitureUseCase(service=service, character_repository=char_repo)


def get_uninstall_furniture_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> UninstallFurnitureUseCaseProtocol:
    return UninstallFurnitureUseCase(service=service, character_repository=char_repo)


def get_house_furniture_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> GetHouseFurnitureUseCaseProtocol:
    return GetHouseFurnitureUseCase(service=service, character_repository=char_repo)


def get_my_furniture_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> GetMyFurnitureUseCaseProtocol:
    return GetMyFurnitureUseCase(service=service, character_repository=char_repo)


def get_update_house_wallpaper_use_case(
    service: HouseServiceProtocol = Depends(get_house_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> UpdateHouseWallpaperUseCaseProtocol:
    return UpdateHouseWallpaperUseCase(service=service, character_repository=char_repo)


def get_knock_house_use_case(
    service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> KnockHouseUseCaseProtocol:
    return KnockHouseUseCase(service=service, character_repository=char_repo)


def get_accept_guest_request_use_case(
    service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> AcceptGuestRequestUseCaseProtocol:
    return AcceptGuestRequestUseCase(service=service, character_repository=char_repo)


def get_reject_guest_request_use_case(
    service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> RejectGuestRequestUseCaseProtocol:
    return RejectGuestRequestUseCase(service=service, character_repository=char_repo)


def get_kick_house_guest_use_case(
    service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> KickHouseGuestUseCaseProtocol:
    return KickHouseGuestUseCase(service=service, character_repository=char_repo)


def get_house_guests_use_case(
    service: HouseGuestServiceProtocol = Depends(get_house_guest_service),
    char_repo: CharacterRepositoryProtocol = Depends(__get_character_repository),
) -> GetHouseGuestsUseCaseProtocol:
    return GetHouseGuestsUseCase(service=service, character_repository=char_repo)


def get_expire_house_requests_use_case_factory(
    session: AsyncSession,
    redis_client,
) -> ExpireHouseRequestsUseCaseProtocol:
    """Factory для Celery tasks"""   

    char_repo = CharacterRepository(session=session)
    collector = BuffsCollector(buff_repository=BuffRepository(session=session))
    modifiers_collector = ModifiersCollector(collectors=[EquipmentCollector(), collector])
    publisher = StatsPublisher(
        redis_client=redis_client,
        character_repository=char_repo,
        modifiers_collector=modifiers_collector,
        buffs_collector=collector,
    )
    service = HouseGuestService(
        house_repository=HouseRepository(session=session),
        character_repository=char_repo,
        guest_request_repository=HouseGuestRequestRepository(session=session),
        guest_session_repository=HouseGuestSessionRepository(session=session),
        furniture_repository=HouseFurnitureRepository(session=session),
        mining_client=get_mining_adapter(settings),
        publisher=publisher,
        settings=settings,
        events=RestEvents(RedisPublisher(redis_client)),
        template_service=RestTemplateService(get_text_template_service()),
        house_events=HouseEvents(RedisPublisher(redis_client)),
        change_location_events=ChangeLocationEvents(RedisPublisher(redis_client)),
    )
    return ExpireHouseRequestsUseCase(service=service)


def get_house_guest_service_factory(
    session: AsyncSession,
    redis_client,
    settings: Settings,
) -> HouseGuestServiceProtocol:
    """Factory для Celery tasks - создаёт HouseGuestService с локальными соединениями"""
    char_repo = CharacterRepository(session=session)
    collector = BuffsCollector(buff_repository=BuffRepository(session=session))
    modifiers_collector = ModifiersCollector(collectors=[EquipmentCollector(), collector])
    publisher = StatsPublisher(
        redis_client=redis_client,
        character_repository=char_repo,
        modifiers_collector=modifiers_collector,
        buffs_collector=collector,
    )
    return HouseGuestService(
        house_repository=HouseRepository(session=session),
        character_repository=char_repo,
        guest_request_repository=HouseGuestRequestRepository(session=session),
        guest_session_repository=HouseGuestSessionRepository(session=session),
        furniture_repository=HouseFurnitureRepository(session=session),
        mining_client=get_mining_adapter(settings),
        publisher=publisher,
        settings=settings,
        events=RestEvents(RedisPublisher(redis_client)),
        template_service=RestTemplateService(get_text_template_service()),
        house_events=HouseEvents(RedisPublisher(redis_client)),
        change_location_events=ChangeLocationEvents(RedisPublisher(redis_client)),
    )


def get_wear_house_furniture_use_case_factory(
    session: AsyncSession,
    redis_client,
) -> WearHouseFurnitureUseCaseProtocol:
    """Factory для Celery tasks"""

    char_repo = CharacterRepository(session=session)
    collector = BuffsCollector(buff_repository=BuffRepository(session=session))
    modifiers_collector = ModifiersCollector(collectors=[EquipmentCollector(), collector])
    publisher = StatsPublisher(
        redis_client=redis_client,
        character_repository=char_repo,
        modifiers_collector=modifiers_collector,
        buffs_collector=collector,
    )
    house_repo = HouseRepository(session=session)
    furniture_repo = HouseFurnitureRepository(session=session)
    guest_session_repo = HouseGuestSessionRepository(session=session)
    mining_client = get_mining_adapter(settings)
    house_events = HouseEvents(RedisPublisher(redis_client))
    house_service = HouseService(
        house_repository=house_repo,
        character_repository=char_repo,
        publisher=publisher,
        settings=settings,
        mining_client=mining_client,
        furniture_repository=furniture_repo,
        events=RestEvents(RedisPublisher(redis_client)),
        template_service=RestTemplateService(get_text_template_service()),
        guest_session_repository=guest_session_repo,
        guest_request_repository=HouseGuestRequestRepository(session=session),
        house_events=house_events,
        change_location_events=ChangeLocationEvents(RedisPublisher(redis_client)),
    )
    return WearHouseFurnitureUseCase(
        session=session,
        settings=settings,
        mining_client=mining_client,
        accumulator_repository=InventoryItemWorkAccumulatorRepository(session=session),
        furniture_repository=furniture_repo,
        house_repository=house_repo,
        guest_session_repository=guest_session_repo,
        house_service=house_service,
        house_events=house_events,
    )