import logging
import uuid

logger = logging.getLogger(__name__)


class DealAutoCancelHandler:
    def __init__(self, redis_subscriber, cancel_deal_factory, session_factory):
        self.redis_subscriber = redis_subscriber
        self.cancel_deal_factory = cancel_deal_factory
        self.session_factory = session_factory
        self.channels = ["online_status_changed", "change_location"]

    async def start_listening(self):
        for channel in self.channels:
            logger.info(f"Subscribing to channel: {channel}")
            await self.redis_subscriber.subscribe(channel, self._handle_event)
        logger.info("Deal auto-cancel handler started listening")

    async def stop_listening(self):
        for channel in self.channels:
            await self.redis_subscriber.unsubscribe(channel)
        logger.info("Deal auto-cancel handler stopped")

    async def _handle_event(self, data: dict):
        try:
            event_type = data.get("event_type")
            event_data = data.get("data", {})

            character_id_str = None
            if isinstance(event_data, dict):
                character_id_str = event_data.get("character_id")
            elif isinstance(event_data, str):
                character_id_str = event_data

            if not character_id_str:
                return

            character_id = uuid.UUID(character_id_str)
            should_cancel = False

            # Событие 1: персонаж ушёл в оффлайн
            if event_type == "online_status_changed":
                if isinstance(event_data, dict) and event_data.get("is_online") is False:
                    should_cancel = True
                    logger.info(f"Character {character_id} went OFFLINE, cancelling deals")

            # Событие 2: персонаж сменил локацию (только если локация ДЕЙСТВИТЕЛЬНО другая)
            elif event_type == "change_location":
                old_slug = event_data.get("old_location_slug")
                new_slug = event_data.get("new_location_slug")

                if not old_slug or not new_slug:
                    old_loc = event_data.get("old_location", {}) or {}
                    new_loc = event_data.get("new_location", {}) or {}
                    old_slug = old_slug or (old_loc.get("slug") if isinstance(old_loc, dict) else None)
                    new_slug = new_slug or (new_loc.get("slug") if isinstance(new_loc, dict) else None)

                if old_slug and new_slug and old_slug != new_slug:
                    should_cancel = True
                    logger.info(f"Character {character_id} moved {old_slug} -> {new_slug}, cancelling deals")
                else:
                    logger.info(f"Character {character_id} location event ignored (not a real move)")

            if not should_cancel:
                return

            # Читаем активные сделки в короткой сессии
            async with self.session_factory() as session:
                from ...deals.repositories import DealRepository
                repo = DealRepository(session=session)
                deals = await repo.list_active_for_character(character_id)

            # Отменяем каждую сделку в ОТДЕЛЬНОЙ сессии (защита от ошибок транзакций)
            cancelled_count = 0
            for deal in deals:
                try:
                    async with self.session_factory() as session:
                        cancel_uc = self.cancel_deal_factory(session)
                        await cancel_uc(deal.id, character_id)
                        cancelled_count += 1
                except Exception as e:
                    logger.warning(f"Failed to auto-cancel deal {deal.id} for {character_id}: {e}")

            logger.info(f"Auto-cancelled {cancelled_count} deals for character {character_id}")

        except ValueError as e:
            logger.error(f"UUID error in deal auto-cancel handler: {e}")
        except Exception:
            logger.exception("Critical error in deal auto-cancel handler")