"""Агрегатор роутеров items.

Реализация эндпоинтов разбита по доменам в apps/items/routes/<домен>.py.
Публичный контракт: mining_app/router.py импортирует
`from .apps.items.routes import router`.

Порядок include_router сохраняет семантику исходного файла:
модуль items (с wildcard-роутами POST /{inventory_item_id}/use
и GET /{item_id}/details) подключается последним.
"""
from fastapi import APIRouter

from . import (
    character,
    crafting,
    crafting_license,
    deals,
    internal,
    items,
    purchase,
    recipes,
    sale,
    settings,
    shop,
    stats,
)

router = APIRouter(prefix='/api/items', tags=['Items'])

# Порядок include_router значим: статичные GET-роуты /city-shop/sales-history,
# /city-shop/settings и /city-shop/stats должны быть зарегистрированы ДО
# wildcard-роута GET /city-shop/{id} (routes/character.py) — иначе Starlette
# отдаёт их под {id}.
router.include_router(deals.router)
router.include_router(internal.router)
router.include_router(recipes.router)
router.include_router(crafting_license.router)
router.include_router(shop.router)
router.include_router(sale.router)
router.include_router(purchase.router)
router.include_router(settings.router)
router.include_router(stats.router)
router.include_router(crafting.router)
router.include_router(character.router)
# items — последним: содержит wildcard-роуты
# POST /{inventory_item_id}/use, GET /{item_id}/details, GET /city-shop/{id}-аналоги
router.include_router(items.router)

