from fastapi import Depends
from shared.permissions import ensure_admin
from shared.schemas.auth import UserTokenDataReadSchema
from .services.admin_mutations import AdminMutationService
from ..pawn_shop.depends import get_economy_events
from ..pawn_shop.events.economy import EconomyEventsProtocol
from ...core.db import Session
from ...core.depends import get_user_token_payload


async def require_admin(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
) -> UserTokenDataReadSchema:
    ensure_admin(token)
    return token


def get_admin_mutation_service(
    session: Session,
    economy_events: EconomyEventsProtocol = Depends(get_economy_events),
) -> AdminMutationService:
    return AdminMutationService(session, economy_events)