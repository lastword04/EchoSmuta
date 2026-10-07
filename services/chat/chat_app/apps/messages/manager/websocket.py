import os
import uuid
import asyncio
from fastapi import WebSocket
from pydantic import ValidationError
import redis.asyncio as redis
from typing import Protocol, Optional, Dict, Set
import json
import logging
from collections import defaultdict

# Ваши импорты сервисов и схем
from ...categories.services.visibility_notifications import CheckVisibilityNotificationsServiceProtocol
from ..services.ignore import IgnoreServiceProtocol
from ..services.settings import ChatSettingsServiceProtocol
from ..schemas import MessageReadSchema
from ..enums import MessageType

logger = logging.getLogger(__name__)


class ConnectionRegistry:
    """Общее на процесс состояние всех WS-подключений.

    WebSocketManager создаётся через Depends на КАЖДОЕ соединение
    (вместе с request-scoped сервисами), поэтому его словари не видят
    соединения других сокетов и dedup-логика в connect() никогда не
    находит дубли между клиентами. Реестр сделан синглтоном на процесс
    (по образцу redis-клиента в core/redis.py) — сервисы с сессиями БД
    остаются request-scoped, а состояние сокетов становится общим.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # conn_id -> WebSocket
        self.character_connections: Dict[str, Set[str]] = defaultdict(set)  # character_id -> set of conn_ids
        self.connection_rooms: Dict[str, str] = {}  # conn_id -> room
        self.connection_locations: Dict[str, str] = {}  # conn_id -> location_slug

        self._stop_events: Dict[str, asyncio.Event] = {}  # conn_id -> Event
        self._listen_tasks: Dict[str, asyncio.Task] = {}  # conn_id -> Task
        self._connect_locks: Dict[str, asyncio.Lock] = {}  # character_id -> Lock


# Словарь реестров: ключ - PID процесса (каждый multiprocessing worker — свой).
_connection_registries: Dict[int, ConnectionRegistry] = {}


def get_connection_registry() -> ConnectionRegistry:
    """Возвращает реестр соединений для ТЕКУЩЕГО процесса."""
    pid = os.getpid()
    if pid not in _connection_registries:
        _connection_registries[pid] = ConnectionRegistry()
    return _connection_registries[pid]


class WebSocketManagerProtocol(Protocol):
    async def connect(self, websocket: WebSocket, character_id: uuid.UUID, room: str) -> str:
        ...

    def disconnect(self, character_id: uuid.UUID, conn_id: str) -> None:
        ...

    async def listen_to_room(self, websocket: WebSocket, character_id: uuid.UUID, room: str, location_slug: Optional[str] = None, conn_id: str = None):
        ...
        
    async def send_to_character(self, character_id: uuid.UUID, message: dict):
        ...

    async def publish_settings_updated(self, character_id: uuid.UUID):
        ...


class WebSocketManager(WebSocketManagerProtocol):
    def __init__(self, redis_client: redis.Redis,
                 ignore_service: IgnoreServiceProtocol,
                 chat_settings_service: ChatSettingsServiceProtocol,
                 visibility_checker: CheckVisibilityNotificationsServiceProtocol,
                 registry: Optional[ConnectionRegistry] = None):
        self.redis = redis_client
        self.ignore_service = ignore_service
        self.chat_settings_service = chat_settings_service
        self.visibility_checker = visibility_checker

        # Реестр соединений ОБЩИЙ на процесс: экземпляр WebSocketManager
        # создаётся FastAPI на каждое WS-соединение, но dedup/рассылка
        # должны видеть подключения из всех сокетов.
        self._registry = registry or get_connection_registry()

        self.active_connections = self._registry.active_connections  # conn_id -> WebSocket
        self.character_connections = self._registry.character_connections  # character_id -> set of conn_ids
        self.connection_rooms = self._registry.connection_rooms  # conn_id -> room
        self.connection_locations = self._registry.connection_locations  # ← conn_id → location_slug

        self._stop_events = self._registry._stop_events  # conn_id -> Event
        self._listen_tasks = self._registry._listen_tasks  # conn_id -> Task
        self._connect_locks = self._registry._connect_locks  # character_id -> Lock

    def _cleanup_connection(self, char_id_str: str, conn_id: str):
        """Вспомогательный метод для гарантированной очистки словарей"""
        self.active_connections.pop(conn_id, None)
        if char_id_str in self.character_connections:
            self.character_connections[char_id_str].discard(conn_id)
            if not self.character_connections[char_id_str]:
                del self.character_connections[char_id_str]
        self.connection_rooms.pop(conn_id, None)
        self.connection_locations.pop(conn_id, None)
        self._stop_events.pop(conn_id, None)
        self._listen_tasks.pop(conn_id, None)    

    async def connect(self, websocket: WebSocket, character_id: uuid.UUID, room: str) -> str:
        await websocket.accept()
        char_id_str = str(character_id)
        
        # Создаём lock для этого персонажа, если его нет
        if char_id_str not in self._connect_locks:
            self._connect_locks[char_id_str] = asyncio.Lock()
        
        # Блокируем, чтобы избежать race condition
        async with self._connect_locks[char_id_str]:
            conn_id = str(uuid.uuid4())

            # Ищем дубль подключения К ТОЙ ЖЕ КОМНАТЕ
            old_conn_id_to_close = None
            for existing_conn_id in self.character_connections.get(char_id_str, set()):
                if self.connection_rooms.get(existing_conn_id) == room:
                    old_conn_id_to_close = existing_conn_id
                    break

            if old_conn_id_to_close:
                logger.debug(f"Closing duplicate for {character_id} in room {room}")
                stop_event = self._stop_events.get(old_conn_id_to_close)
                if stop_event: 
                    stop_event.set()
                
                old_task = self._listen_tasks.get(old_conn_id_to_close)
                if old_task and not old_task.done():
                    old_task.cancel()
                    try:
                        await old_task
                    except asyncio.CancelledError:
                        pass
                
                # ✅ ЗАКРЫВАЕМ СТАРЫЙ WEBSOCKET
                old_ws = self.active_connections.get(old_conn_id_to_close)
                if old_ws:
                    try:
                        await old_ws.close(code=1000, reason="Duplicate connection")
                    except Exception as e:
                        logger.debug(f"Failed to close old websocket: {e}")
                
                self._cleanup_connection(char_id_str, old_conn_id_to_close)

            # Регистрируем новое подключение
            self.active_connections[conn_id] = websocket
            self.character_connections[char_id_str].add(conn_id)
            self.connection_rooms[conn_id] = room
            self._stop_events[conn_id] = asyncio.Event()
            
            logger.debug(f"WebSocket connected for {character_id} (room: {room}, conn_id: {conn_id})")
            return conn_id

    def disconnect(self, character_id: uuid.UUID, conn_id: str):
        char_id_str = str(character_id)

        # Сигнализируем остановку именно этой задачи
        stop_event = self._stop_events.get(conn_id)
        if stop_event:
            stop_event.set()

        # Cancel old listen_to_room task
        old_task = self._listen_tasks.get(conn_id)
        if old_task and not old_task.done():
            old_task.cancel()

        # Очищаем словари через хелпер
        self._cleanup_connection(char_id_str, conn_id)
        logger.debug(f"WebSocket disconnected for {character_id} (conn_id: {conn_id})")

    async def send_to_character(self, character_id: uuid.UUID, message: dict):
        char_id_str = str(character_id)
        conn_ids = self.character_connections.get(char_id_str, set())
        msg_text = json.dumps(message)
        
        # Рассылаем всем активным сокетам этого персонажа
        for conn_id in list(conn_ids):
            ws = self.active_connections.get(conn_id)
            if ws:
                try:
                    await ws.send_text(msg_text)
                except Exception as e:
                    logger.error(f"Failed to send to {character_id} (conn {conn_id}): {e}")

    async def publish_settings_updated(self, character_id: uuid.UUID):
        """Публикует событие обновления настроек, чтобы открытые соединения
        перечитали их без переподключения."""
        await self.redis.publish(
            f"chat_settings_updated_{character_id}",
            json.dumps({"event_type": "chat_settings_updated"}),
        )

    async def listen_to_room(self, websocket: WebSocket, character_id: uuid.UUID, room: str, location_slug: Optional[str] = None, conn_id: str = None):
        if not conn_id:
            logger.error("listen_to_room called without conn_id")
            return
            
        char_id_str = str(character_id)
        self._listen_tasks[conn_id] = asyncio.current_task()
        
        # ✅ Сохраняем локацию подключения
        if location_slug:
            self.connection_locations[conn_id] = location_slug

        stop_event = self._stop_events.get(conn_id)
        if not stop_event:
            stop_event = asyncio.Event()
            self._stop_events[conn_id] = stop_event

        chat_settings = await self.chat_settings_service.get_by_character_id(character_id)

        pubsub = self.redis.pubsub()
        room_channels = [
            f"chat_room_{room}",
            f"mail_notifications_{character_id}",
            f"force_disconnect_{character_id}",
            "chat_room_presence",
            f"chat_settings_updated_{character_id}",
            "economy_state_updated",
            "chat_room_house",
            "chat_room_rest",
        ]

        # Приватные сообщения доставляются через единственный главный сокет.
        # Иначе chat- и deals-сокеты одного персонажа получают одну публикацию
        # из chat_room_private и оба отправляют её клиенту.
        if room == "global":
            room_channels.append("chat_room_private")

        # Вариант A: один сокет обслуживает обе вкладки чата,
        # поэтому локационный канал нужен ВСЕГДА (фильтрация — на клиенте)
        if room == "global" and location_slug:
            room_channels.append(f"chat_room_{location_slug}")

        if room == "global" and chat_settings.filter_system_messages:
            room_channels.append("chat_room_system")

        await pubsub.subscribe(*room_channels)
        logger.info(f"User {character_id} subscribed to rooms: {room_channels}")

        try:
            while not stop_event.is_set():
                # Проверяем актуальность соединения по conn_id
                if self.active_connections.get(conn_id) is not websocket:
                    logger.info(f"WebSocket for {character_id} became stale, stopping")
                    break

                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=0.1
                    )

                    if message is None:
                        await asyncio.sleep(0.01)
                        continue

                    if message["type"] != "message":
                        continue
                    # Настройки чата изменились — перечитываем снимок на лету,
                    # без пересоздания соединения
                    channel = message.get("channel")
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    if channel == f"chat_settings_updated_{character_id}":
                        old_filter_system = chat_settings.filter_system_messages
                        chat_settings = await self.chat_settings_service.get_by_character_id(character_id)
                        # Подписки не должны застывать: синхронизируем канал system
                        # с новым значением настройки без переподключения
                        if room == "global" and chat_settings.filter_system_messages != old_filter_system:
                            if chat_settings.filter_system_messages:
                                await pubsub.subscribe("chat_room_system")
                                logger.info(f"Subscribed to chat_room_system for {character_id}")
                            else:
                                await pubsub.unsubscribe("chat_room_system")
                                logger.info(f"Unsubscribed from chat_room_system for {character_id}")
                        logger.info(f"Chat settings reloaded for {character_id}")
                        continue

                    if self.active_connections.get(conn_id) is not websocket:
                        logger.info(f"Connection changed during message processing for {character_id}")
                        break

                    try:
                        raw_data = json.loads(message["data"])

                        if isinstance(raw_data, dict) and raw_data.get("event_type") in ("character_online", "character_location"):
                            # ✅ Обновляем локацию при перемещении персонажа
                            if raw_data.get("event_type") == "character_location":
                                new_location_slug = raw_data.get("new_location_slug")
                                old_location_slug = raw_data.get("old_location_slug")
                                if new_location_slug:
                                    event_char_id = str(raw_data.get("character_id", ""))
                                    for cid in list(self.character_connections.get(event_char_id, set())):
                                        self.connection_locations[cid] = new_location_slug
                                        
                                        # Переподписка: это событие О НАС — меняем локационный канал
                                        if event_char_id == str(character_id):
                                            if old_location_slug:
                                                await pubsub.unsubscribe(f"chat_room_{old_location_slug}")
                                                logger.debug(f"Unsubscribed from old location: {old_location_slug}")
                                            if new_location_slug:
                                                await pubsub.subscribe(f"chat_room_{new_location_slug}")
                                                logger.debug(f"Subscribed to new location: {new_location_slug}")
                                            logger.info(f"Resubscribed {character_id}: {old_location_slug} → {new_location_slug}")
                            
                            if self.active_connections.get(conn_id) is websocket:
                                await websocket.send_text(json.dumps(raw_data))
                                logger.debug(f"Presence event sent to {character_id}: {raw_data.get('event_type')}")
                            continue

                        if isinstance(raw_data, dict) and raw_data.get("event_type", "").startswith("deal_"):
                            # Данные события находятся внутри поля "data"
                            event_data = raw_data.get("data", {})
                            if isinstance(event_data, dict):
                                initiator_id = event_data.get("initiator_character_id")
                                partner_id = event_data.get("partner_character_id")
                                
                                # Отправляем событие ОБОИМ участникам сделки
                                if str(character_id) == str(initiator_id) or str(character_id) == str(partner_id):
                                    if self.active_connections.get(conn_id) is websocket:
                                        await websocket.send_text(json.dumps(raw_data))
                                        logger.debug(f"Deal event sent to {character_id}: {raw_data.get('event_type')}")
                            continue

                        # ✅ Обработка обновления экономики
                        if isinstance(raw_data, dict) and raw_data.get("event_type") == "economy_state_updated":
                            event_data = raw_data.get("data", {})
                            if isinstance(event_data, dict):
                                initiator_id = event_data.get("initiator_character_id")
                                partner_id = event_data.get("partner_character_id")
                                location_slug = event_data.get("location_slug")
                                action = event_data.get("action")
                                
                                client_location = self.connection_locations.get(conn_id)
                                
                                should_send = False
                                
                                if location_slug and action in [
                                    "sale_item_created", "sale_item_removed", "sale_price_updated",
                                    "shop_item_added", "shop_item_removed",
                                    "shop_info_updated", "shop_photo_updated",
                                    "lot_created", "lot_sold", "lot_cancelled",
                                    "buyout_stock_updated", "buyout_prices_updated",
                                    "mining_finished",
                                ]:
                                    same_location = client_location == location_slug
                                    if action in ["mining_finished", "buyout_stock_updated"]:
                                        # ✅ mining_finished и buyout_stock_updated получает и инициатор (обновление своего UI),
                                        # и остальные персонажи в той же локации
                                        if same_location:
                                            should_send = True
                                    elif same_location and str(character_id) != str(initiator_id):
                                        # ✅ Остальные экономические события — всем в локации, кроме инициатора
                                        should_send = True
                                
                                elif str(character_id) == str(initiator_id) or str(character_id) == str(partner_id):
                                    should_send = True
                                
                                if should_send:
                                    if self.active_connections.get(conn_id) is websocket:
                                        await websocket.send_text(json.dumps(raw_data))
                                        logger.debug(f"Economy state update sent to {character_id}: action={action}, location={location_slug}")
                            continue      

                        # ✅ Обработка обновления состояния дома
                        if isinstance(raw_data, dict) and raw_data.get("event_type") == "house_state_updated":
                            event_data = raw_data.get("data", {})
                            if isinstance(event_data, dict):
                                target_id = raw_data.get("target_character_id")
                                
                                # Отправляем только тому, кому адресовано
                                if str(character_id) == str(target_id):
                                    if self.active_connections.get(conn_id) is websocket:
                                        await websocket.send_text(json.dumps(raw_data))
                                        logger.debug(f"House state update sent to {character_id}: {raw_data.get('data', {}).get('action')}")
                            continue

                        # Rest state (гостиница): broadcast всем подписанным
                        # на chat_room_rest. Внутри data приходит location_slug —
                        # фронт сам сверит со своей локацией и сделает refetch.
                        if isinstance(raw_data, dict) and raw_data.get("event_type") == "rest_state_updated":
                            if self.active_connections.get(conn_id) is websocket:
                                await websocket.send_text(json.dumps(raw_data))
                                logger.debug(f"Rest state update sent to {character_id}")
                            continue

                        if isinstance(raw_data, dict) and raw_data.get("event_type") == "new_mail":
                            if self.active_connections.get(conn_id) is websocket:
                                await websocket.send_text(json.dumps(raw_data))
                                logger.debug(f"New mail notification sent to {character_id}")
                            continue

                        msg_data = MessageReadSchema(**raw_data)

                        if not chat_settings.chat_enabled:
                            continue

                        only_me_and_my_filter = chat_settings.filter_only_me_and_my
                        is_own_message = msg_data.sender_id == character_id
                        is_for_user = (
                            msg_data.target_user_ids and
                            character_id in msg_data.target_user_ids
                        )

                        if only_me_and_my_filter and not (is_own_message or is_for_user):
                            logger.debug(f"Message filtered by 'only me and my' for {character_id}: {msg_data.id}")
                            continue

                        target_user_ids = msg_data.target_user_ids if msg_data.target_user_ids else []
                        can_show = (msg_data.room != "private") or (character_id in target_user_ids) or (character_id == msg_data.sender_id)

                        logger.debug(f"Message filtering for {character_id}: room={msg_data.room}, target_users={target_user_ids}, can_show_initial={can_show}")

                        if msg_data.sender_id and msg_data.message_type != MessageType.SYSTEM_PLAY_CHARACTER:
                            ignored_result = await self.ignore_service.get_ignored_characters(character_id, [msg_data.sender_id])

                            if self.active_connections.get(conn_id) is not websocket:
                                logger.info(f"Connection changed during ignore check for {character_id}")
                                break

                            is_ignored = len(ignored_result) != 0
                            can_show = can_show and not is_ignored
                            logger.debug(f"Ignoring check for {character_id}: is_ignored={is_ignored}, can_show={can_show}")

                        if msg_data.is_trade:
                            can_show = can_show and chat_settings.filter_trade_messages
                            logger.debug(f"Trade filtering for {character_id}: show={chat_settings.filter_trade_messages}, can_show={can_show}")

                        if msg_data.room == "system":
                            system_messages_enabled = chat_settings.filter_system_messages
                            is_targeted_system_message = (
                                msg_data.message_type in [MessageType.SYSTEM_PRIVATE, MessageType.SYSTEM_PLAY_CHARACTER]
                                or msg_data.target_user_ids is not None
                            )

                            if is_targeted_system_message:
                                can_show = can_show and system_messages_enabled and is_for_user
                                logger.debug(f"Targeted system filtering for {character_id}: show={system_messages_enabled}, is_for_user={is_for_user}, can_show={can_show}")
                            else:
                                can_show = can_show and system_messages_enabled
                                logger.debug(f"System filtering for {character_id}: show={system_messages_enabled}, can_show={can_show}")

                        if can_show:
                            if self.active_connections.get(conn_id) is websocket:
                                await websocket.send_text(str(msg_data.model_dump_json()))
                                logger.debug(f"Message sent to {character_id}: {msg_data.id}")
                        else:
                            logger.debug(f"Message filtered out for {character_id}: {msg_data.id}")

                    except ValidationError as e:
                        logger.error(f"Validation error from Redis: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing message for {character_id}: {e}")
                        continue

                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    logger.debug(f"Listen loop cancelled for {character_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in message loop for {character_id}: {e}")
                    await asyncio.sleep(0.5)
                    continue

        except Exception as e:
            logger.error(f"Error in listen_to_room for {character_id}: {e}")
            raise
        finally:
            try:
                await asyncio.shield(pubsub.unsubscribe(*room_channels))
            except Exception as e:
                logger.debug(f"pubsub unsubscribe error for {character_id}: {e}")
            try:
                if hasattr(pubsub, "aclose"):
                    await asyncio.shield(pubsub.aclose())
                else:
                    await asyncio.shield(pubsub.close())
            except Exception as e:
                logger.debug(f"pubsub close error for {character_id}: {e}")
            logger.info(f"User {character_id} unsubscribed from rooms: {room_channels}")
