"""WebSocket endpoint для real-time обновлений статов персонажа"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import redis.asyncio as aioredis
import asyncio
import json
import logging
import time
from typing import Dict, List

from ....settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting
MAX_CONNECTIONS_PER_CHARACTER = 10

# Heartbeat
HEARTBEAT_TIMEOUT = 90  # секунд (3 missed heartbeats)


class ConnectionManager:
    """Менеджер WebSocket соединений по character_id"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[dict]] = {}
    
    async def connect(self, websocket: WebSocket, character_id: str):
        await websocket.accept()
        if character_id not in self.active_connections:
            self.active_connections[character_id] = []
        
        self.active_connections[character_id].append({
            'ws': websocket,
            'last_heartbeat': time.time()
        })
    
    def disconnect(self, websocket: WebSocket, character_id: str):
        if character_id in self.active_connections:
            self.active_connections[character_id] = [
                conn for conn in self.active_connections[character_id]
                if conn['ws'] != websocket
            ]
            
            if not self.active_connections[character_id]:
                del self.active_connections[character_id]
    
    def get_connection_count(self, character_id: str) -> int:
        """Получить количество активных подключений"""
        if character_id not in self.active_connections:
            return 0
        
        current_time = time.time()
        self.active_connections[character_id] = [
            conn for conn in self.active_connections[character_id]
            if conn['ws'].client_state == WebSocketState.CONNECTED
            and (current_time - conn['last_heartbeat']) < HEARTBEAT_TIMEOUT
        ]
        
        if not self.active_connections[character_id]:
            del self.active_connections[character_id]
            return 0
        
        return len(self.active_connections[character_id])
    
    async def send_to_character(self, character_id: str, message: dict):
        """Отправляет сообщение всем соединениям конкретного персонажа."""
        connections = self.active_connections.get(character_id)
        if not connections:
            return

        disconnected = []
        for conn in connections:
            ws = conn['ws']
            try:
                if ws.client_state != WebSocketState.CONNECTED:
                    disconnected.append(ws)
                    continue

                await ws.send_json(message)
                conn['last_heartbeat'] = time.time()
            except Exception as e:
                logger.warning(f"[WS] Failed to send: {e}")
                disconnected.append(ws)

        if disconnected:
            current = self.active_connections.get(character_id, [])
            remaining = [conn for conn in current if conn['ws'] not in disconnected]

            if remaining:
                self.active_connections[character_id] = remaining
            elif character_id in self.active_connections:
                del self.active_connections[character_id]


manager = ConnectionManager()


@router.websocket("/ws/character/{character_id}/stats")
async def character_stats_ws(websocket: WebSocket, character_id: str):
    """WebSocket endpoint для real-time обновлений статов."""
    
    current_count = manager.get_connection_count(character_id)
    
    if current_count >= MAX_CONNECTIONS_PER_CHARACTER:
        await websocket.close(code=1008, reason="Too many connections")
        return
    
    pubsub = None
    r = None
    
    try:
        await manager.connect(websocket, character_id)
        
        r = aioredis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True
        )
        
        pubsub = r.pubsub()
        channel = f"character:{character_id}:stats"
        
        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.send_to_character(character_id, data)
                except Exception as e:
                    logger.error(f"[WS] Error processing message: {e}", exc_info=True)
                    break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS] Error for {character_id}: {e}", exc_info=True)
    finally:
        try:
            if pubsub:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
        except Exception:
            pass
        
        try:
            if r:
                await r.aclose()
        except Exception:
            pass
        
        manager.disconnect(websocket, character_id)


@router.on_event("startup")
async def startup_event():
    """Запускаем фоновую задачу очистки мёртвых соединений"""
    asyncio.create_task(cleanup_dead_connections_periodically())


async def cleanup_dead_connections_periodically():
    """Периодически очищает мёртвые соединения каждые 60 секунд"""
    while True:
        await asyncio.sleep(60)
        
        current_time = time.time()
        
        for character_id in list(manager.active_connections.keys()):
            dead = [
                conn for conn in manager.active_connections[character_id]
                if conn['ws'].client_state != WebSocketState.CONNECTED
                or (current_time - conn['last_heartbeat']) > HEARTBEAT_TIMEOUT
            ]
            
            if dead:
                manager.active_connections[character_id] = [
                    conn for conn in manager.active_connections[character_id]
                    if conn not in dead
                ]
                
                if not manager.active_connections[character_id]:
                    del manager.active_connections[character_id]