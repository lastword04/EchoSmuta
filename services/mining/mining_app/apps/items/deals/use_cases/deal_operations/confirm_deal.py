import uuid
from datetime import UTC, datetime
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ...enums import DealStatus
from ...exceptions import (
    DealEmptyOfferError,
    DealNotFoundError,
    DealNotReadyError,
    DealPartnerDepartedError,
    DealPartnerOfflineError,
    DealPartnerWeightLimitError,
    DealSelfWeightLimitError,
)
from ...repositories import (
    DealItemRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
)
from ...schemas import DealReadSchema
from ._base import (
    _character_id,
    _DealUseCase,
    _goods_prices,
    _publish_deal_event,
    _validate_deal_economy,
)
from .complete_deal import CompleteDealUseCaseProtocol


class ConfirmDealUseCaseProtocol(UseCaseProtocol[DealReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema) -> DealReadSchema: ...


class ConfirmDealUseCase(_DealUseCase, ConfirmDealUseCaseProtocol):
    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, complete_use_case: CompleteDealUseCaseProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository, self.offer_repository, self.item_repository, self.complete_use_case = repository, offer_repository, item_repository, complete_use_case
        self.deal_events = deal_events

    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema) -> DealReadSchema:
        character_id = _character_id(user)
        should_complete = False
        async with self.repository.session.begin():
            deal = await self.repository.get_for_participant(deal_id, character_id, for_update=True)
            if not deal:
                raise DealNotFoundError(deal_id)

            # 1. Сначала проверка СВОЕГО предложения
            offers = await self.offer_repository.get_by_deal(deal.id, for_update=True)
            offer = next((value for value in offers if value.character_id == character_id), None)
            if offer is None:
                raise DealEmptyOfferError()

            all_items = await self.item_repository.get_by_deal(deal.id, for_update=True)
            participant_items = [item for item in all_items if item.owner_character_id == character_id]
            if not participant_items and not (offer.ducats_escrowed > 0 or offer.gold_escrowed > 0):
                raise DealEmptyOfferError()

            # 2. Статус партнёра: ушёл / оффлайн
            partner_id = deal.partner_character_id if character_id == deal.initiator_character_id else deal.initiator_character_id
            online = await self._online_at_location(deal.location_slug)
            online_ids = {character.id for character in online.objects}
            if partner_id not in online_ids:
                partner = await self.character_client.get_full_character(partner_id)
                if partner.location_slug != deal.location_slug:
                    raise DealPartnerDepartedError()
                raise DealPartnerOfflineError()

            # 3. Сделка принята партнёром И у партнёра что-то выставлено
            if deal.status != DealStatus.ACTIVE:
                raise DealNotReadyError()

            partner_offer = next((value for value in offers if value.character_id == partner_id), None)
            partner_items = [item for item in all_items if item.owner_character_id == partner_id]
            if partner_offer is None or (not partner_items and not (partner_offer.ducats_escrowed > 0 or partner_offer.gold_escrowed > 0)):
                raise DealNotReadyError()
            # 🎭 Роли сделки и цена
            item_prices, resource_prices = await _goods_prices(self.repository.session, all_items)
            _validate_deal_economy(deal, offers, all_items, item_prices, resource_prices)

            # 🛡️ Проверка весов ВНУТРИ транзакции (перед завершением)
            for recipient_id in (deal.initiator_character_id, deal.partner_character_id):
                balance = await self.character_client.get_character_weight_balance(recipient_id)
                incoming = await self.item_repository.incoming_weight(deal.id, recipient_id)
                if balance.weight + incoming > balance.max_weight:
                    if recipient_id == character_id:
                        raise DealSelfWeightLimitError()
                    else:
                        raise DealPartnerWeightLimitError()

            offer.confirmed_revision = offer.revision
            if character_id == deal.initiator_character_id:
                deal.initiator_confirmed_at = datetime.now(UTC)
            else:
                deal.partner_confirmed_at = datetime.now(UTC)
            should_complete = all(value.confirmed_revision == value.revision for value in offers)
        
        await _publish_deal_event(self.deal_events, deal, DealEventType.CONFIRMED)
        if should_complete:
            return await self.complete_use_case(deal_id)
        return DealReadSchema.model_validate(deal)
