import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from mining_app.settings import settings

from ....resources.events.publisher_sync import RedisPublisherSyncProtocol
from ...adapters.characters_sync import CharacterServiceSyncClient
from ..enums import DealCurrency, DealLedgerOperationKind, DealStatus
from ..models import Deal, DealLedgerOperation
from ..repositories_sync import (
    DealItemSyncRepository,
    DealLedgerOperationSyncRepository,
    DealOfferSyncRepository,
    DealResourceReservationSyncRepository,
    DealSyncRepository,
    TradeLicenseSyncRepository,
)

logger = logging.getLogger(__name__)

DEAL_LIFETIME = timedelta(minutes=30)
_OPERATION_NAMESPACE = uuid.UUID("1bdbf5e3-82c8-43ee-89fb-6b794ce1ebbd")

def _operation_id(deal_id: uuid.UUID, name: str) -> uuid.UUID:
    return uuid.uuid5(_OPERATION_NAMESPACE, f"{deal_id}:{name}")

class CompleteDealSyncUseCase:
    def __init__(self, character_service: CharacterServiceSyncClient, redis_publisher: RedisPublisherSyncProtocol | None = None):
        self.character_service = character_service
        self.redis_publisher = redis_publisher
        self.deal_tax = Decimal(str(settings.trade_license.deal_tax))
        self.discounted_tax = Decimal(str(settings.trade_license.deal_tax_discounted))

    def __call__(self, session: Session, deal_id: uuid.UUID) -> Deal:
        deal_repo = DealSyncRepository(session)
        offer_repo = DealOfferSyncRepository(session)
        item_repo = DealItemSyncRepository(session)
        reservation_repo = DealResourceReservationSyncRepository(session)
        ledger_repo = DealLedgerOperationSyncRepository(session)
        license_repo = TradeLicenseSyncRepository(session)

        with session.begin():
            deal = deal_repo.get_for_update(deal_id)
            if not deal:
                raise ValueError("Deal not found")
            offers = offer_repo.get_by_deal(deal.id, for_update=True)
            items = item_repo.get_by_deal(deal.id, for_update=True)

            if deal.status == DealStatus.COMPLETED:
                return deal
            if deal.status not in (DealStatus.ACTIVE, DealStatus.COMPLETING) or len(offers) != 2:
                raise ValueError("Deal not ready for completion")

            # Проверка веса
            for recipient_id in (deal.initiator_character_id, deal.partner_character_id):
                balance = self.character_service.get_character_weight_balance(recipient_id)
                incoming = item_repo.incoming_weight(deal.id, recipient_id)
                if balance.weight + incoming > balance.max_weight:
                    raise ValueError("Recipient inventory weight limit exceeded")

            deal.status = DealStatus.COMPLETING
            session.flush()

        # Завершаем транзакцию (теперь всё в одной транзакции!)
        with session.begin():
            deal = deal_repo.get_for_update(deal_id)
            if not deal or deal.status != DealStatus.COMPLETING:
                raise ValueError("Deal completion interrupted")
            offers = offer_repo.get_by_deal(deal.id, for_update=True)
            items = item_repo.get_by_deal(deal.id, for_update=True)

            # Передача денег (теперь внутри транзакции!)
            payouts = []
            for offer in offers:
                recipient_id = deal.partner_character_id if offer.character_id == deal.initiator_character_id else deal.initiator_character_id
                license_ = license_repo.get_for_character(recipient_id)
                tax_rate = self.discounted_tax if license_ and license_.end_date > datetime.now(UTC) else self.deal_tax
                ducats_tax = (offer.ducats_escrowed * tax_rate).quantize(Decimal("0.01"))
                gold_tax = (offer.gold_escrowed * tax_rate).quantize(Decimal("0.01"))
                for currency, amount, tax_amount in ((DealCurrency.DUCATS, offer.ducats_escrowed, ducats_tax), (DealCurrency.GOLD, offer.gold_escrowed, gold_tax)):
                    if not amount:
                        continue
                    income = amount - tax_amount
                    if income:
                        op_id = _operation_id(deal.id, f"{recipient_id}:{currency.value}:income")
                        if currency == DealCurrency.DUCATS:
                            self.character_service.credit_ducats(
                                recipient_id, income, op_id,
                                "deal_ducats_transfer_income", "mining.deals",
                                item_meta={"deal_id": str(deal.id), "offer_character_id": str(offer.character_id)}
                            )
                        else:
                            self.character_service.credit_gold(
                                recipient_id, income, op_id,
                                "deal_gold_transfer_income", "mining.deals",
                                {"deal_id": str(deal.id), "offer_character_id": str(offer.character_id)}
                            )
                        payouts.append((recipient_id, currency, income, op_id))

            item_repo.transfer_assets(deal, items)
            reservation_repo.mark_transferred_for_deal(deal.id)

            operations = []
            for offer in offers:
                recipient_id = deal.partner_character_id if offer.character_id == deal.initiator_character_id else deal.initiator_character_id
                license_ = license_repo.get_for_character(recipient_id)
                tax_rate = self.discounted_tax if license_ and license_.end_date > datetime.now(UTC) else self.deal_tax
                for currency, amount in ((DealCurrency.DUCATS, offer.ducats_escrowed), (DealCurrency.GOLD, offer.gold_escrowed)):
                    if amount:
                        op_id = _operation_id(deal.id, f"{recipient_id}:{currency.value}:income")
                        operations.append(
                            DealLedgerOperation(
                                deal_id=deal.id,
                                operation_id=op_id,
                                operation_kind=DealLedgerOperationKind.TRANSFER,
                                character_id=recipient_id,
                                counterparty_id=offer.character_id,
                                currency=currency,
                                amount=amount,
                                status='APPLIED'
                            )
                        )
                        tax_amount = (amount * tax_rate).quantize(Decimal("0.01"))
                        if tax_amount:
                            operations.append(
                                DealLedgerOperation(
                                    deal_id=deal.id,
                                    operation_id=_operation_id(deal.id, f"{recipient_id}:{currency.value}:tax"),
                                    operation_kind=DealLedgerOperationKind.TAX,
                                    character_id=recipient_id,
                                    counterparty_id=offer.character_id,
                                    currency=currency,
                                    amount=tax_amount,
                                    status='APPLIED'
                                )
                            )
            ledger_repo.create_many(operations)
            deal.status = DealStatus.COMPLETED
            deal.completed_at = datetime.now(UTC)
            session.commit()
            
            # Публикация события для фронта (WS)
            if self.redis_publisher:
                try:
                    payload = {
                        "event_type": "economy_state_updated",
                        "data": {
                            "action": "deal_completed",
                            "initiator_character_id": str(deal.initiator_character_id),
                            "partner_character_id": str(deal.partner_character_id),
                            "location_slug": deal.location_slug,
                            "deal_id": str(deal.id),
                        }
                    }
                    self.redis_publisher.publish("economy_state_updated", payload)
                except Exception as e:
                    logger.error(f"Failed to publish deal_completed economy state update: {e}")
        
        return deal


class ExpireDealSyncUseCase:
    def __init__(self, character_service: CharacterServiceSyncClient, redis_publisher: RedisPublisherSyncProtocol | None = None):
        self.character_service = character_service
        self.redis_publisher = redis_publisher

    def __call__(self, session: Session, limit: int = 50) -> int:
        deal_repo = DealSyncRepository(session)
        offer_repo = DealOfferSyncRepository(session)
        item_repo = DealItemSyncRepository(session)
        reservation_repo = DealResourceReservationSyncRepository(session)        

        now = datetime.now(UTC)
        with session.begin():
            deals = deal_repo.list_expired_for_update(now, limit)
            for deal in deals:
                offers = offer_repo.get_by_deal(deal.id, for_update=True)
                for offer in offers:
                    for currency, amount in ((DealCurrency.DUCATS, offer.ducats_escrowed), (DealCurrency.GOLD, offer.gold_escrowed)):
                        if amount:
                            op_id = _operation_id(deal.id, f"{offer.character_id}:{currency.value}:expire-refund")
                            if currency == DealCurrency.DUCATS:
                                self.character_service.credit_ducats(
                                    offer.character_id, amount, op_id,
                                    "deal_ducats_escrow_expire_refund", "mining.deals",
                                    {"deal_id": str(deal.id)}
                                )
                            else:
                                self.character_service.credit_gold(
                                    offer.character_id, amount, op_id,
                                    "deal_gold_escrow_expire_refund", "mining.deals",
                                    {"deal_id": str(deal.id)}
                                )
                            session.add(
                                DealLedgerOperation(
                                    deal_id=deal.id,
                                    operation_id=op_id,
                                    operation_kind=DealLedgerOperationKind.ESCROW_RELEASE,
                                    character_id=offer.character_id,
                                    currency=currency,
                                    amount=amount,
                                    status='APPLIED'
                                )
                            )
                reservation_repo.release_active_for_deal(deal.id)
                item_repo.clear_inventory_deal_id(deal.id)
                deal.status = DealStatus.EXPIRED
                
                # Публикация события для каждой истёкшей сделки
                if self.redis_publisher:
                    try:
                        payload = {
                            "event_type": "economy_state_updated",
                            "data": {
                                "action": "deal_expired",
                                "initiator_character_id": str(deal.initiator_character_id),
                                "partner_character_id": str(deal.partner_character_id),
                                "location_slug": deal.location_slug,
                                "deal_id": str(deal.id),
                            }
                        }
                        self.redis_publisher.publish("economy_state_updated", payload)
                    except Exception as e:
                        logger.error(f"Failed to publish deal_expired economy state update: {e}")
            
            session.commit()
            return len(deals)


class RecoverCompletingDealsSyncUseCase:
    def __init__(self, complete_use_case: CompleteDealSyncUseCase):
        self.complete_use_case = complete_use_case

    def __call__(self, session: Session, limit: int = 50) -> int:
        deal_repo = DealSyncRepository(session)
        deals = deal_repo.list_completing(limit)
        session.commit() 
        completed = 0
        for deal in deals:
            self.complete_use_case(session, deal.id)
            completed += 1
        return completed