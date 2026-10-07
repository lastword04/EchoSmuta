# Архитектура торговых локаций

## Обзор

Все торговые локации получают команды от TopBar через `topBarActionsSlice` (Redux). Обработка команд зависит от сложности локации.

## Простые локации (TradeHallPage, PawnShopPage)

Используют `useLocationPageController` — простое переключение вкладок через Redux `select`.

**Характеристики:**
- Все вкладки в одной физической локации
- Нет смены `character.location_slug`
- Простое переключение UI без бэкенд-запросов

## Сложные локации (CityTradeLocation)

Кастомная логика `handleViewChange` из-за:
- Физической смены локации (аптека → лаборатория)
- Разных типов мастерских (production vs non-production)
- Суб-навигации внутри вкладок

**Слушают `topBarActionsSlice` напрямую**, но обрабатывают через свою логику.

## Общие helpers

Общие функции в `src/shared/lib/navigation/navigationHelpers.js`:
- `shouldRefreshOnSameView(currentView, targetView)` — клик на ту же вкладку = рефреш
- `isWorkshopTransition(fromSlug, toSlug)` — проверка перехода мастерская ↔ родитель

## Паттерн

Это **Strategy**, а не нарушение архитектуры:
- `topBarActionsSlice` — координация (что кликнули)
- `useLocationPageController` — стратегия "простая навигация"
- `CityTradeLocation.handleViewChange` — стратегия "сложная навигация"