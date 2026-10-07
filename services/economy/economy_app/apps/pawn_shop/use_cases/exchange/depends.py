from fastapi import Depends

from .....core.clients.characters_client import CharactersClient
from .....core.clients.depends import get_characters_client, get_mining_client
from .....core.clients.mining_client import MiningClient
from ...depends import get_economy_events, get_economy_template_service
from ...events.economy import EconomyEventsProtocol
from ...services.economy_templates import EconomyTemplateServiceProtocol
from .cancel import CancelExchangeLotUseCase
from .create import CreateExchangeLotUseCase
from .deal import DealExchangeLotUseCase


def get_create_exchange_lot_use_case(
    characters_client: CharactersClient = Depends(get_characters_client),
    mining_client: MiningClient = Depends(get_mining_client),
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
) -> CreateExchangeLotUseCase:
    return CreateExchangeLotUseCase(characters_client, mining_client, economy_events)


def get_cancel_exchange_lot_use_case(
    characters_client: CharactersClient = Depends(get_characters_client),
    mining_client: MiningClient = Depends(get_mining_client),
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
) -> CancelExchangeLotUseCase:
    return CancelExchangeLotUseCase(characters_client, mining_client, economy_events)


def get_deal_exchange_lot_use_case(
    characters_client: CharactersClient = Depends(get_characters_client),
    mining_client: MiningClient = Depends(get_mining_client),
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
    template_service: EconomyTemplateServiceProtocol = Depends(get_economy_template_service),
) -> DealExchangeLotUseCase:
    return DealExchangeLotUseCase(characters_client, mining_client, economy_events, template_service)