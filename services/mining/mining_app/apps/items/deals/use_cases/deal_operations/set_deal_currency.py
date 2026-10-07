import uuid
from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.deal_events import DealEventType

from ......core.use_cases import UseCaseProtocol
from ....adapters.characters import CharacterServiceClientProtocol
from ....events.deals import DealEventsProtocol
from ...enums import (
    DealCurrency,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
)
from ...exceptions import (
    DealBothSidesMoneyError,
    DealGoldTradeDisabledError,
    DealInsufficientFundsError,
    DealMixedOfferError,
    DealNotFoundError,
    DealStateError,
)
from ...models import DealLedgerOperation
from ...repositories import (
    DealItemRepositoryProtocol,
    DealLedgerOperationRepositoryProtocol,
    DealOfferRepositoryProtocol,
    DealRepositoryProtocol,
)
from ...schemas import DealCurrencyOfferUpdateSchema, DealOfferReadSchema
from ._base import _character_id, _DealUseCase, _publish_deal_event


class SetDealCurrencyUseCase(_DealUseCase):
    currency: DealCurrency
    amount_field: str
    escrow_field: str

    def __init__(self, repository: DealRepositoryProtocol, offer_repository: DealOfferRepositoryProtocol, item_repository: DealItemRepositoryProtocol, ledger_repository: DealLedgerOperationRepositoryProtocol, character_client: CharacterServiceClientProtocol, deal_events: DealEventsProtocol) -> None:
        super().__init__(character_client)
        self.repository = repository
        self.offer_repository = offer_repository
        self.item_repository = item_repository
        self.ledger_repository = ledger_repository
        self.deal_events = deal_events

    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema, data: DealCurrencyOfferUpdateSchema) -> DealOfferReadSchema:
        character_id = _character_id(user)
        async with self.repository.session.begin():
            existing = await self.ledger_repository.get_by_operation_id(data.operation_id)
            if existing:
                offer = await self.offer_repository.get_for_character(deal_id, character_id)
                if not offer:
                    raise DealNotFoundError(deal_id)
                return DealOfferReadSchema.model_validate(offer)
            deal, offer = await self._prepare_offer(self.repository, self.offer_repository, deal_id, character_id)
            if data.amount < 0:
                raise DealStateError("Amount cannot be negative")
            if self.currency == DealCurrency.GOLD:
                privileges = await self.character_client.get_trade_privileges(character_id)
                if not privileges.gold_trade_enabled:
                    raise DealGoldTradeDisabledError()      
            current_amount = getattr(offer, self.amount_field)
            delta = data.amount - current_amount
            if delta > 0:
                my_items = await self.item_repository.get_by_deal(deal.id)
                if any(it.owner_character_id == character_id for it in my_items):
                    raise DealMixedOfferError()
                offers_for_check = await self.offer_repository.get_by_deal(deal.id)
                partner_offer_check = next((o for o in offers_for_check if o.character_id != character_id), None)
                if partner_offer_check and (partner_offer_check.ducats_escrowed > 0 or partner_offer_check.gold_escrowed > 0):
                    raise DealBothSidesMoneyError()
                # 🛡️ Проверка баланса до эскроу
                if self.currency == DealCurrency.DUCATS:
                    balance = await self.character_client.get_simple_character_balance(character_id)
                    if balance.ducats < abs(delta):
                        raise DealInsufficientFundsError()
                else:
                    full = await self.character_client.get_full_character(character_id)
                    gold = getattr(full, "gold", None)
                    if gold is not None and gold < abs(delta):
                        raise DealInsufficientFundsError()
            if delta:
                operation_type = f"deal_{self.currency.value.lower()}_escrow_{'hold' if delta > 0 else 'release'}"
                item_meta = {"deal_id": str(deal.id), "offer_id": str(offer.id)}
                partner_id = (
                    deal.partner_character_id
                    if offer.character_id == deal.initiator_character_id
                    else deal.initiator_character_id
                )
                client_method = getattr(self.character_client, f"{'debit' if delta > 0 else 'credit'}_{self.currency.value.lower()}")
                await client_method(
                    character_id,
                    abs(delta),
                    data.operation_id,
                    operation_type,
                    "mining.deals",
                    counterparty_id=partner_id,
                    item_meta=item_meta,
                )
                self.repository.session.add(DealLedgerOperation(
                    deal_id=deal.id,
                    operation_id=data.operation_id,
                    operation_kind=DealLedgerOperationKind.ESCROW_HOLD if delta > 0 else DealLedgerOperationKind.ESCROW_RELEASE,
                    character_id=character_id,
                    counterparty_id=partner_id,
                    currency=self.currency,
                    amount=abs(delta),
                    status=DealLedgerOperationStatus.APPLIED,
                    payload={"operation_type": operation_type, "source": "mining.deals", "item_meta": item_meta}
                ))
            setattr(offer, self.amount_field, data.amount)
            setattr(offer, self.escrow_field, data.amount)
            self._touch_offer(deal, offer, await self.offer_repository.get_by_deal(deal.id, for_update=True))
        await _publish_deal_event(self.deal_events, deal, DealEventType.UPDATED, {"currency": self.currency.value, "amount": data.amount})
        return DealOfferReadSchema.model_validate(offer)


class SetDealDucatsUseCaseProtocol(UseCaseProtocol[DealOfferReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema, data: DealCurrencyOfferUpdateSchema) -> DealOfferReadSchema: ...


class SetDealDucatsUseCase(SetDealCurrencyUseCase, SetDealDucatsUseCaseProtocol):
    currency = DealCurrency.DUCATS
    amount_field = "ducats_amount"
    escrow_field = "ducats_escrowed"


class SetDealGoldUseCaseProtocol(UseCaseProtocol[DealOfferReadSchema], Protocol):
    async def __call__(self, deal_id: uuid.UUID, user: UserTokenDataReadSchema, data: DealCurrencyOfferUpdateSchema) -> DealOfferReadSchema: ...


class SetDealGoldUseCase(SetDealCurrencyUseCase, SetDealGoldUseCaseProtocol):
    currency = DealCurrency.GOLD
    amount_field = "gold_amount"
    escrow_field = "gold_escrowed"


