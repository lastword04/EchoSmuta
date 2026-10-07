import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from ....adapters.characters import CharacterServiceClientProtocol
from ....events.items import ItemEventsProtocol
from ....exceptions import InsufficientCharacterDucatsForCityTradeShopError
from ....services.adapters.item_templates import ItemTemplateServiceProtocol
from ...exceptions import DealStateError
from ...models import TradeLicense
from ...repositories import TradeLicenseRepositoryProtocol
from ...schemas import TradeLicenseStatusSchema

logger = logging.getLogger(__name__)


class TradeLicenseUseCase:
    def __init__(self, repository: TradeLicenseRepositoryProtocol, character_client: CharacterServiceClientProtocol, items_events: "ItemEventsProtocol", template_service: "ItemTemplateServiceProtocol", renewal_cost: int, renewal_days: int, deal_tax: float, discounted_tax: float, exchange_tax: float, discounted_exchange_tax: float) -> None:
        self.repository, self.character_client = repository, character_client
        self.items_events, self.template_service = items_events, template_service
        self.renewal_cost, self.renewal_days = renewal_cost, renewal_days
        self.deal_tax, self.discounted_tax = Decimal(str(deal_tax)), Decimal(str(discounted_tax))
        self.exchange_tax, self.discounted_exchange_tax = Decimal(str(exchange_tax)), Decimal(str(discounted_exchange_tax))

    async def status(self, character_id: uuid.UUID) -> TradeLicenseStatusSchema:
        result = await self.repository.session.execute(
            text("SELECT character_id, end_date FROM trade_licenses WHERE character_id = :cid"),
            {"cid": str(character_id)}
        )
        row = result.fetchone()
        if row is None:
            active = False
            end_date = None
        else:
            end_date = row[1]
            active = end_date > datetime.now(UTC)
        return TradeLicenseStatusSchema(
            character_id=character_id,
            active=active,
            end_date=end_date,
            deal_tax_rate=self.discounted_tax if active else self.deal_tax,
            exchange_tax_rate=self.discounted_exchange_tax if active else self.exchange_tax
        )

    async def renew(self, character_id: uuid.UUID) -> TradeLicenseStatusSchema:
        # 🛡️ Проверка уровня: лицензия доступна с 3-го уровня
        character = await self.character_client.get_simple_info_character(character_id)
        if character.level < 3:
            raise DealStateError("Лицензия торговца доступна с 3-го уровня")

        # 🛡️ Проверка баланса ДО списания (иначе character-сервис кинет 409)
        balance = await self.character_client.get_simple_character_balance(character_id)
        if balance.ducats < self.renewal_cost:
            raise InsufficientCharacterDucatsForCityTradeShopError(
                required_ducats=self.renewal_cost,
                current_ducats=balance.ducats,
            )

        now = datetime.now(UTC)
        async with self.repository.session.begin():
            result = await self.repository.session.execute(
                text("SELECT end_date FROM trade_licenses WHERE character_id = :cid"),
                {"cid": str(character_id)}
            )
            row = result.fetchone()
            current_end_date = row[0] if row else None
            active = bool(current_end_date and current_end_date > now)
            end_date = (current_end_date if active else now) + timedelta(days=self.renewal_days)

            stmt = insert(TradeLicense).values(
                character_id=character_id,
                end_date=end_date,
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now
            )
            stmt = stmt.on_conflict_do_update(
                constraint='trade_licenses_character_id_key',
                set_={'end_date': end_date, 'updated_at': now}
            )
            await self.repository.session.execute(stmt)

            await self.character_client.debit_ducats(
                character_id,
                self.renewal_cost,
                uuid.uuid4(),
                "trade_license_renewal" if active else "trade_license_purchase",
                "mining.trade_license",
                None,
                {"end_date": end_date.isoformat()}
            )
            # Публикуем системное сообщение
            end_date_str = end_date.strftime("%d.%m.%Y %H:%M")
            try:
                if active:
                    message_content = self.template_service.get_trade_license_renewal_message(end_date_str)
                    event_type = "trade_license_renewal"
                else:
                    message_content = self.template_service.get_trade_license_purchase_message()
                    event_type = "trade_license_purchase"
                
                await self.items_events.publish_message(ItemMessageEventSchema(
                    event_type=event_type,
                    character_id=character_id,
                    location_slug="1.27.trade-hall",
                    content=message_content,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character_id],
                    is_trade=False,
                ))
            except Exception as e:
                logger.warning("Failed to send trade license message: %s", e)
        return await self.status(character_id)
