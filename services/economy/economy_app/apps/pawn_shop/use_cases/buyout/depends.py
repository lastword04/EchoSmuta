from fastapi import Depends

from .....core.clients.characters_client import CharactersClient
from .....core.clients.depends import get_characters_client, get_mining_client
from .....core.clients.mining_client import MiningClient
from ...depends import get_economy_events, get_economy_template_service
from ...events.economy import EconomyEventsProtocol
from ...services.economy_templates import EconomyTemplateServiceProtocol
from .buy import BuyResourceFromBuyoutUseCase
from .sell import SellResourceToBuyoutUseCase


def get_buy_resource_from_buyout_use_case(
    characters_client: CharactersClient = Depends(get_characters_client),
    mining_client: MiningClient = Depends(get_mining_client),
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
    template_service: EconomyTemplateServiceProtocol = Depends(get_economy_template_service),
) -> BuyResourceFromBuyoutUseCase:
    return BuyResourceFromBuyoutUseCase(characters_client, mining_client, economy_events, template_service)


def get_sell_resource_to_buyout_use_case(
    characters_client: CharactersClient = Depends(get_characters_client),
    mining_client: MiningClient = Depends(get_mining_client),
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
    template_service: EconomyTemplateServiceProtocol = Depends(get_economy_template_service),
) -> SellResourceToBuyoutUseCase:
    return SellResourceToBuyoutUseCase(characters_client, mining_client, economy_events, template_service)