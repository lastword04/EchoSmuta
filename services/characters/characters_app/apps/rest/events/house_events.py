import uuid
from datetime import datetime, timezone
from typing import Protocol

from .publisher import RedisPublisherProtocol


def _json_safe(obj):
    """Рекурсивно приводит объект к JSON-сериализуемому виду.

    Нужно для house_payload: внутри вложены UUID (id дома, inventory_item_id,
    character_id) и datetime. json.dumps их не умеет — падает с TypeError.
    Приводим локально, не трогая другие места (там с UUID работает Pydantic
    через response_model, а здесь — сырой JSON в Redis).
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


class HouseEventsProtocol(Protocol):
    async def publish(
        self,
        action: str,
        house_id: uuid.UUID,
        target_user_ids: list[uuid.UUID],
        affected_character_id: uuid.UUID | None = None,
        house_payload: dict | None = None,
    ) -> None: ...


class HouseEvents(HouseEventsProtocol):
    """События состояния дома для живого обновления UI через WebSocket.

    Канал house_events консумируется чат-сервисом и доставляется
    перечисленным target_user_ids.

    affected_character_id — «главный герой» события, если он есть:
      - guest_accepted: кого приняли (гость)
      - guest_kicked:   кого выгнали (гость)
      - guest_left:     кто вышел (гость)
    Для furniture_changed / wallpaper_changed / guest_knocked — None.

    house_payload — полный payload дома (CurrentHouseReadSchema), нужен
    только при guest_accepted, чтобы фронт гостя сразу отрисовал дом
    без ожидания refetch getHousesStatus.
    """

    def __init__(self, publisher: RedisPublisherProtocol):
        self.publisher = publisher

    async def publish(
        self,
        action: str,
        house_id: uuid.UUID,
        target_user_ids: list[uuid.UUID],
        affected_character_id: uuid.UUID | None = None,
        house_payload: dict | None = None,
    ) -> None:
        event_data = {
            "event_type": "house_state_updated",
            "data": {
                "action": action,
                "house_id": str(house_id),
                "target_user_ids": [str(u) for u in target_user_ids],
                "affected_character_id": str(affected_character_id) if affected_character_id else None,
                "house_payload": _json_safe(house_payload) if house_payload else None,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.publisher.publish("house_events", event_data)