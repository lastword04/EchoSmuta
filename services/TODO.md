## Mail WebSocket - будущие улучшения

- [ ] Добавить heartbeat (ping/pong) каждые 30 секунд для стабильности соединений
- [ ] Настроить Nginx для WebSocket (proxy_read_timeout 86400)
- [ ] Добавить звуковое уведомление при получении письма
- [ ] Показывать toast "Новое письмо от {sender_name}"
- [ ] Мониторинг: метрики по количеству WebSocket соединений
- [ ] Graceful shutdown: закрывать WebSocket при logout

=== АДМИНКА (расширение /admin) ===

Уже готово:
✅ Ledger (GET /api/characters/admin/characters/currency-operations)
✅ Торговые права (GET/PATCH /api/characters/admin/characters/{id}/trade-privileges)
✅ Зависшие сделки (GET /api/items/admin/deals/completing)
✅ Админ-аккаунт (lastword04@yandex.ru, role=ADMIN)
✅ Скрипт scripts/make_admin.py в users

Разделы по мере появления доменов:
⏳ Управление персонажами (поиск, бан, изменение дукатов) — characters
⏳ Управление пользователями (поиск, бан) — users
⏳ Логи входов (IP, время, персонаж) — auth + characters
⏳ Таблицы ресурсов (CRUD) — mining
⏳ Таблицы предметов (CRUD) — mining
⏳ Таблицы локаций + настройки — mining + locations
⏳ Биржа (лоты, цены) — economy
⏳ Палатки/магазины — mining
⏳ Модерация чата — chat (когда появится)
⏳ Логи боевой системы — (когда появится)
⏳ Аналитика/графики — все сервисы
⏳ Audit log действий админов — все сервисы

Архитектура:
- НЕ новый микросервис
- Админ-эндпоинты в существующих сервисах с ensure_admin(token)
- Единый фронтенд /admin с боковым меню
- Паттерн: 1 раздел = 1-2 эндпоинта + 1 React-компонент