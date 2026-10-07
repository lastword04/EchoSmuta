from fastapi import Depends
from ...core.clients.characters_client import CharactersClient
from ...core.clients.depends import get_characters_client
from ...core.db import Session
from ..pawn_shop.depends import get_economy_events, get_economy_template_service
from ..pawn_shop.events.economy import EconomyEventsProtocol
from ..pawn_shop.services.economy_templates import EconomyTemplateServiceProtocol
from .use_cases.buy_meal import BuyMealUseCase
from .use_cases.get_meals import GetMealsUseCase


def get_meals_use_case(session: Session) -> GetMealsUseCase:
    return GetMealsUseCase(session)


def get_buy_meal_use_case(
    characters_client: CharactersClient = Depends(get_characters_client),
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
    template_service: EconomyTemplateServiceProtocol = Depends(get_economy_template_service),
) -> BuyMealUseCase:
    return BuyMealUseCase(characters_client, economy_events, template_service)