"""Провайдеры deals-домена: сделки, торговые лицензии, Celery/event-фабрики.

Репозитории сделок живут в apps/items/deals/repositories.py (не в items/repositories),
поэтому их провайдеры объявлены здесь же. TradeLicenseUseCase тоже определён в
deals/use_cases/deals.py — вместе с настройками trade_license (deal_tax/exchange_tax).
"""
import redis
from fastapi import Depends

from ....core.db import AsyncSession, get_async_session
from ....settings import Settings, get_settings
from ...resources.depends import get_redis_publisher
from ...resources.events.publisher import RedisPublisher, RedisPublisherProtocol
from ..adapters.characters import CharacterServiceClient, CharacterServiceClientProtocol
from ..deals.repositories import (
    DealItemRepository,
    DealItemRepositoryProtocol,
    DealLedgerOperationRepository,
    DealLedgerOperationRepositoryProtocol,
    DealOfferRepository,
    DealOfferRepositoryProtocol,
    DealRepository,
    DealRepositoryProtocol,
    DealResourceReservationRepository,
    DealResourceReservationRepositoryProtocol,
    TradeLicenseRepository,
    TradeLicenseRepositoryProtocol,
)
from ..deals.use_cases import (
    AcceptDealUseCase,
    AcceptDealUseCaseProtocol,
    AddDealInventoryItemUseCase,
    AddDealInventoryItemUseCaseProtocol,
    AddDealResourceUseCase,
    AddDealResourceUseCaseProtocol,
    CancelDealUseCase,
    CancelDealUseCaseProtocol,
    CompleteDealUseCase,
    CompleteDealUseCaseProtocol,
    ConfirmDealUseCase,
    ConfirmDealUseCaseProtocol,
    CreateDealUseCase,
    CreateDealUseCaseProtocol,
    GetDealUseCase,
    GetDealUseCaseProtocol,
    ListCompletingDealsUseCase,
    ListDealsUseCase,
    ListDealsUseCaseProtocol,
    ListNearbyPartnersUseCase,
    ListNearbyPartnersUseCaseProtocol,
    RemoveDealItemUseCase,
    RemoveDealItemUseCaseProtocol,
    SetDealDucatsUseCase,
    SetDealDucatsUseCaseProtocol,
    SetDealGoldUseCase,
    SetDealGoldUseCaseProtocol,
    TradeLicenseUseCase,
)
from ..events.deals import DealEvents, DealEventsProtocol
from ..events.items import ItemEventsProtocol
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from .adapters import get_character_service_client, get_item_template_service
from .events import get_deal_events, get_items_events


# deal repositories
def _get_deal_repository(session: AsyncSession = Depends(get_async_session)) -> DealRepositoryProtocol:
    return DealRepository(session=session)


def _get_deal_offer_repository(session: AsyncSession = Depends(get_async_session)) -> DealOfferRepositoryProtocol:
    return DealOfferRepository(session=session)


def _get_deal_item_repository(session: AsyncSession = Depends(get_async_session)) -> DealItemRepositoryProtocol:
    return DealItemRepository(session=session)


def _get_deal_resource_reservation_repository(
    session: AsyncSession = Depends(get_async_session),
) -> DealResourceReservationRepositoryProtocol:
    return DealResourceReservationRepository(session=session)


def _get_deal_ledger_operation_repository(
    session: AsyncSession = Depends(get_async_session),
) -> DealLedgerOperationRepositoryProtocol:
    return DealLedgerOperationRepository(session=session)


def _get_trade_license_repository(session: AsyncSession = Depends(get_async_session)) -> TradeLicenseRepositoryProtocol:
    return TradeLicenseRepository(session=session)


def get_create_deal_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> CreateDealUseCaseProtocol:
    return CreateDealUseCase(repository, offer_repository, character_client, deal_events)


def get_accept_deal_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> AcceptDealUseCaseProtocol:
    return AcceptDealUseCase(repository, character_client, deal_events)


def get_list_deals_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
) -> ListDealsUseCaseProtocol:
    return ListDealsUseCase(repository)


def get_deal_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
) -> GetDealUseCaseProtocol:
    return GetDealUseCase(repository, offer_repository, item_repository)


def get_list_nearby_partners_use_case(
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
) -> ListNearbyPartnersUseCaseProtocol:
    return ListNearbyPartnersUseCase(character_client)


def get_cancel_deal_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
    reservation_repository: DealResourceReservationRepositoryProtocol = Depends(_get_deal_resource_reservation_repository),
    ledger_repository: DealLedgerOperationRepositoryProtocol = Depends(_get_deal_ledger_operation_repository),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
) -> CancelDealUseCaseProtocol:
    return CancelDealUseCase(repository, offer_repository, item_repository, reservation_repository, ledger_repository, deal_events, character_client)


def get_complete_deal_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
    reservation_repository: DealResourceReservationRepositoryProtocol = Depends(_get_deal_resource_reservation_repository),
    ledger_repository: DealLedgerOperationRepositoryProtocol = Depends(_get_deal_ledger_operation_repository),
    license_repository: TradeLicenseRepositoryProtocol = Depends(_get_trade_license_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    settings: Settings = Depends(get_settings),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> CompleteDealUseCaseProtocol:
    return CompleteDealUseCase(repository, offer_repository, item_repository, reservation_repository, ledger_repository, license_repository, character_client, settings.trade_license.deal_tax, settings.trade_license.deal_tax_discounted, deal_events, redis_publisher)


def get_confirm_deal_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
    complete_use_case: CompleteDealUseCaseProtocol = Depends(get_complete_deal_use_case),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> ConfirmDealUseCaseProtocol:
    return ConfirmDealUseCase(repository, offer_repository, item_repository, complete_use_case, character_client, deal_events)


def get_trade_license_use_case(
    repository: TradeLicenseRepositoryProtocol = Depends(_get_trade_license_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    settings: Settings = Depends(get_settings),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
) -> TradeLicenseUseCase:
    config = settings.trade_license
    return TradeLicenseUseCase(
        repository,
        character_client,
        items_events,
        template_service,
        config.renewal_cost,
        config.renewal_days,
        config.deal_tax,
        config.deal_tax_discounted,
        config.exchange_tax,
        config.exchange_tax_discounted
    )


def get_list_completing_deals_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
) -> ListCompletingDealsUseCase:
    return ListCompletingDealsUseCase(repository)


def get_set_deal_ducats_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),  # ← ДОБАВИТЬ
    ledger_repository: DealLedgerOperationRepositoryProtocol = Depends(_get_deal_ledger_operation_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> SetDealDucatsUseCaseProtocol:
    return SetDealDucatsUseCase(repository, offer_repository, item_repository, ledger_repository, character_client, deal_events)


def get_set_deal_gold_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),  # ← ДОБАВИТЬ
    ledger_repository: DealLedgerOperationRepositoryProtocol = Depends(_get_deal_ledger_operation_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> SetDealGoldUseCaseProtocol:
    return SetDealGoldUseCase(repository, offer_repository, item_repository, ledger_repository, character_client, deal_events)


def get_add_deal_resource_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
    reservation_repository: DealResourceReservationRepositoryProtocol = Depends(_get_deal_resource_reservation_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> AddDealResourceUseCaseProtocol:
    return AddDealResourceUseCase(repository, offer_repository, item_repository, reservation_repository, character_client, deal_events)


def get_add_deal_inventory_item_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> AddDealInventoryItemUseCaseProtocol:
    return AddDealInventoryItemUseCase(repository, offer_repository, item_repository, character_client, deal_events)


def get_remove_deal_item_use_case(
    repository: DealRepositoryProtocol = Depends(_get_deal_repository),
    offer_repository: DealOfferRepositoryProtocol = Depends(_get_deal_offer_repository),
    item_repository: DealItemRepositoryProtocol = Depends(_get_deal_item_repository),
    reservation_repository: DealResourceReservationRepositoryProtocol = Depends(_get_deal_resource_reservation_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    deal_events: DealEventsProtocol = Depends(get_deal_events),
) -> RemoveDealItemUseCaseProtocol:
    return RemoveDealItemUseCase(repository, offer_repository, item_repository, reservation_repository, character_client, deal_events)


# Закрытие сделки если ушел
def get_cancel_deal_actions_factory():
    """Фабрика для создания CancelDealUseCase в фоновых задачах (без Depends)"""
    def factory(session) -> CancelDealUseCaseProtocol:

        settings = get_settings()

        # Создаем клиент и паблишер вручную, так как мы вне контекста запроса
        character_client = CharacterServiceClient(
            base_url=settings.character_service_app.base_url,
            stats_base_url=settings.character_service_app.stats_base_url,
        )

        redis_client = redis.Redis(**settings.redis.to_connection_kwargs())
        redis_publisher = RedisPublisher(redis_client)
        deal_events = DealEvents(redis_publisher)

        return CancelDealUseCase(
            repository=DealRepository(session=session),
            offer_repository=DealOfferRepository(session=session),
            item_repository=DealItemRepository(session=session),
            reservation_repository=DealResourceReservationRepository(session=session),
            ledger_repository=DealLedgerOperationRepository(session=session),
            deal_events=deal_events,
            character_client=character_client,
        )
    return factory
