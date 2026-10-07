# shared/hooks — глобальные хуки приложения

Единое место для хуков, потребители которых находятся в **двух и более слоях**
(pages, widgets, features, shared/hoc). Реорганизовано в рамках рефакторинга структуры
(этапы A–C, 09.2026): сессионные оркестраторы вынесены в `app/providers/hooks/`,
доменные хуки — в `entities/` и `widgets/`, конфиги локаций понижены в
`shared/config/locations/`. Все рёбра «shared → app» устранены.

## Структура папок

shared/hooks/
├── location/ ← навигация и префетчи локаций (4 хука)
├── ui/ ← UI-хелперы: размер шрифта, ошибки, тема (5 хуков)
└── README.md



## Правило размещения хука

Хук живёт на **низшем слое, где находятся все его потребители**:

| Потребители хука | Где лежит |
|---|---|
| 2+ слоя (pages + widgets + hoc и т.п.) | `shared/hooks/` (эта папка) |
| только одна фича | `features/<фича>/hooks/` |
| только один виджет | `widgets/<виджет>/hooks/` |
| домен сущности | `entities/<сущность>/hooks/` |

Хуки этой папки не должны знать о виджетах, страницах и фичах.

## ⚠️ Осознанный компромисс: импорты из entities и app

Ребра «shared → app» устранены полностью (понижение конфигов в `shared/config/locations/`
+ DI). Остались только восходящие импорты в `entities/*/api` — они зафиксированы ниже.
**Список зафиксирован, пополнять без обсуждения нельзя:**

| Хук/Файл | Расположение | Импортирует из entities | Импортирует из app | Обоснование |
|---|---|---|---|---|
| `useRefreshCurrentView.js` | shared/hooks/location/ | — (передается через DI) | — | Потребители инжектят apiSlice аргументом |
| `viewPrefetches.js` | shared/config/locations/ | 8 api-слайсов (inventory, captcha, resources, economy, character, tavern, rest, chat) | — | Реестр RTK-запросов, оркестрирует префетчи для всех локаций |
| `defaultViewPrefetches.js` | shared/config/locations/ | те же api-слайсы | — | Дефолтные префетчи при входе в локацию |

**Чистые хуки (без восходящих импортов):** `useAutoFontSize`, `useErrorToast`, `useEscapeKey`, `useMediaQuery`, `useTheme`, `useLocationNavigation`, `useLocationPageController`, `useViewEntryPrefetches` (конфиги локаций теперь в `shared/config/locations/`, импортируются легально).


## 🛡️ Архитектурное решение (ADR): Реестры префетчей

Файлы `shared/config/locations/viewPrefetches.js` и `defaultViewPrefetches.js`
импортируют RTK-слайсы из `entities/*/api`. Это **осознанное решение, а не
технический долг**.

**Почему это сделано именно так:**
1. Это паттерн **Registry** (Реестр). Его задача — декларативно связывать
   абстрактные ключи UI с конкретными реализациями API. Реестр по определению
   обязан знать о том, что он регистрирует.
2. Попытка устранить эту связь через Dependency Injection (передачу api-слайсов
   аргументами через все слои) приведёт к **оверинжинирингу**: ухудшение
   типизации, раздувание сигнатур хуков, усложнение отладки — без практической
   пользы.
3. Слой `shared/config` в FSD допускает знание о `entities` для целей глобальной
   конфигурации приложения.

**Строгое правило:** рефакторинг этих файлов с целью внедрения DI для
API-слайсов **запрещён**. Текущая реализация является финальной и оптимальной.


## Сессионные оркестраторы (app/providers/hooks/)

Хуки, которые оркестрируют глобальное состояние сессии, WebSocket-подключения и готовность страницы. Живут в `app/providers/hooks/`, так как слой `app` имеет право импортировать из `entities` и `shared`.

**Текущий состав:**
- `useEconomyWebSocket` — глобальные слушатели economy-событий
- `usePresenceSync` — синхронизация присутствия через WS
- `ChatWebSocketProvider` — провайдер контекста чата (контракт в `shared/lib/context/ChatWebSocketContext.js`)
- `useBaseRefresh` — базовая логика обновления данных
- `useAtomicPageReady` — контроль готовности страницы к показу
- `useLocationTransition` — обработка переходов между локациями
- `useModalState` — управление модальными окнами и меню

**Доменные хуки чата:**
- `useChatSend` — отправка сообщений (живёт в `entities/chat/hooks/`)

## Доменные хуки, перенесенные из shared
Эти хуки были перенесены из `shared/hooks/` в свои доменные слои для соблюдения FSD:

- `useVisitTracking` → `entities/auth/hooks/` (трекинг визитов)
- `useShopStatus` → `entities/items/hooks/` (статус лавки/лицензии)
- `useLocationTopBarState` → `widgets/TopBar/hooks/` (состояние верхней панели)

## Конфиги локаций (shared/config/locations/)
Конфигурационные файлы, пониженные из `app/locations/` в `shared/config/locations/`:

- `tradeConfig.js` — статические данные торговой локации (из `features/city-trade/config/`)
- `locationNavConfig.js` — конфигурация кнопок TopBar для всех локаций
- `viewEntryPrefetches.js` — реестр RTK-запросов для префетча вкладок
- `locationEntryPrefetches.js` — дефолтные префетчи при входе в локацию

Эти конфиги имеют восходящие импорты в `entities/*/api`, что зафиксировано в таблице компромиссов выше.

## Соглашения

- Один хук = один файл `useXxx.js` (`.jsx` только если файл содержит JSX).
- Хуки-сиблинги импортируют друг друга по `./useXxx`.
- Путь до `shared/*` из этой папки: `../../` (пример: `../../lib/websocket/ChatWebSocket`).
- Путь до `src/*`: `../../../` (пример: `../../../entities/chat/api/chatApi`).
- Новые восходящие импорты (в entities) — только с добавлением строки в таблицу выше.
  Ребра «shared → app» запрещены безусловно: конфиги уже понижены в `shared/config/locations/`,
  сессионные оркестраторы живут в `app/providers/hooks/`.