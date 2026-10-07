/**
 * Конфигурация инвалидации кэшей при событии 'economy-updated' от WebSocket.
 * 
 * Источник события: бэкенд (микросервисы economy, mining, shop).
 * Слушатель: useEconomyWebSocket.js (app/providers/hooks).
 * 
 * БАЗОВАЯ ИНВАЛИДАЦИЯ (при любом action):
 * - characterApi: ['Character']
 * - economyApi: ['Economy', 'Lots', 'Market', 'Resources']
 * - resourcesApi: ['Resources', 'MiningStatus', 'Economy']
 * - inventoryApi: ['StartedCrafting', 'WorkshopRecipes']
 * 
 * УСЛОВНАЯ ИНВАЛИДАЦИЯ ДЛЯ ТОРГОВЛИ:
 * См. useEconomyWebSocket.js — динамический список на основе
 * action, shop_id и location_slug (не вынесена сюда, слишком специфична).
 */

/**
 * Возвращает теги для базовой инвалидации при событии economy-updated.
 * Используется в useEconomyWebSocket.js (handleEconomyUpdate и handleResync).
 */
export const getBaseEconomyInvalidationTags = () => ({
  characterApi: ['Character'],
  economyApi: ['Economy', 'Lots', 'Market', 'Resources'],
  resourcesApi: ['Resources', 'MiningStatus', 'Economy'],
  inventoryApi: ['StartedCrafting', 'WorkshopRecipes'],
});

/**
 * Возвращает теги для массовой инвалидации после обрыва WebSocket (resync).
 * Используется в useEconomyWebSocket.js (handleResync).
 */
export const getEconomyResyncInvalidationTags = () => ({
  characterApi: ['Character', 'LocationsStats'],
  economyApi: ['Economy', 'Lots', 'Market'],
  resourcesApi: ['Resources', 'MiningStatus', 'Economy'],
  inventoryApi: [
    'Inventory',
    'ShopsList',
    'CityShop',
    'ShopItems',
    'SalesHistory',
    'Deals',
    'Deal',
  ],
  chatApi: ['OnlineUsers'],
});