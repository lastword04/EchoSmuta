"""Доменные роутеры приложения персонажей.

Каждый модуль пакета создаёт собственный ``APIRouter`` без префикса;
общий префикс ``/api/characters`` и тег ``Characters`` добавляются здесь.
"""
from fastapi import APIRouter

from .character import router as character_router
from .skills import router as skills_router
from .economy import router as economy_router
from .attachment import router as attachment_router
from .referrals import router as referrals_router
from .locations import router as locations_router
from .info import router as info_router
from .game import router as game_router
from .internal import router as internal_router
from .valid import router as valid_router
from .websocket import router as websocket_router

router = APIRouter(prefix='/api/characters', tags=['Characters'])

# ВАЖНО: порядок include_router влияет на разрешение маршрутов Starlette.
# Параметрический GET /{character_id} (character_router) должен
# регистрироваться ПОСЛЕ всех статических односегментных путей
# (/me, /online, /detach, /attachment-settings, /referral-link, /my-info,
# /skills/ ...), иначе они будут перехватываться им и отвечать 422.
# Поэтому character_router идёт предпоследним.
router.include_router(skills_router)
router.include_router(info_router)
router.include_router(attachment_router)
router.include_router(referrals_router)
router.include_router(locations_router)
router.include_router(economy_router)
router.include_router(game_router)
router.include_router(internal_router)
# valid_router (GET /{character_id}/is-online) регистрируется до character_router,
# чтобы параметрический путь /{character_id} не перехватывал /is-online.
router.include_router(valid_router)
router.include_router(character_router)

# WebSocket регистрируется отдельно (без префикса /api/characters),
# чтобы сохранить рабочий путь wss://<host>/ws/character/{id}/stats,
# на который ссылается фронтенд (CHARACTER_WS_BASE_URL).

__all__ = ['router', 'websocket_router']
