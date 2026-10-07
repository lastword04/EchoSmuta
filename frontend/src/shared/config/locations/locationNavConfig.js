// src/shared/config/locations/locationNavConfig.js

import { 
  getTradeLocationConfig  
} from './tradeConfig';
import { isTradeLocation } from './locations'; 

// Экспортируем, чтобы CityTradeLocation тоже использовал этот маппинг, а не свой локальный
export const WORKSHOP_TO_PARENT_MAP = {
  '1.35.laboratory': '1.9.pharmacy',
  '1.36.kitchen': '1.25.fish-shop',
  '1.37.carpentry-workshop': '1.21.furniture-shop',
  '1.38.hunter-workshop': '1.22.hunting-shop',
  '1.39.incubator': '1.24.bird-market',
};

// Унифицированная функция нормализации 
export const normalizeViewId = (id) => {
  if (!id) return null;
  const validViews = [
    "licenses", "workshop", "recipes", "your-recipes", 
    "your-shop", "shops", "shop-detail", "sales-history", 
    "buyout", "exchange",
    "tents", "deals", "your-tent",
    "resources",
  ];
  if (validViews.includes(id)) return id;
  if (id.includes("your-")) return "your-shop";
  return "shops";
};

// Порядок поиска кнопок: override → tradeConfig.
// Override — нейтральный механизм для локаций вне торговой системы.
// tradeConfig — просто один из источников, не «дефолт».
const LOCATIONS_OVERRIDES = {
  '1.26.pawn-shop': {    
    buttons: [
      { id: 'buyout', label: 'Скупка' },
      { id: 'exchange', label: 'Биржа ресурсов' }
    ]
  },
  // Будущие локации добавляются сюда за 10 секунд
};

// Чистая функция получения базовых данных (без Redux!)
export const getBaseLocationConfig = (locationSlug) => {
  if (!locationSlug) return { parentSlug: null, isWorkshop: false, isProduction: false, navLabels: {}, buttons: [] };

  const parentSlug = WORKSHOP_TO_PARENT_MAP[locationSlug] || locationSlug;
  const isWorkshop = locationSlug !== parentSlug;

  const tradeConfig = getTradeLocationConfig(parentSlug);
  const override = LOCATIONS_OVERRIDES[locationSlug];

  return {
    parentSlug,
    isWorkshop,
    isProduction: tradeConfig?.isProduction || false,
    navLabels: tradeConfig?.navLabels || {},
    // Кнопки: сначала override, затем tradeConfig, иначе пусто.
    // Ни один источник не «по умолчанию» — просто порядок поиска.
    buttons: override?.buttons ?? tradeConfig?.buttons ?? [],
  };
};


/**
 * Определяет начальную вкладку для локации.
 * Чистая функция, не зависит от Redux — может вызываться синхронно
 * в момент клика для мгновенного переключения TopBar.
 */
export const getInitialView = (locationSlug) => {
  if (!locationSlug) return null;

   // Ресурсные локации
  const RESOURCE_LOCATIONS = [
    '2.1.swamp',
    '2.5.forest', 
    '2.4.lake',
    '2.6.sands',
    '2.3.mine',
    '2.2.shaft'
  ];
  if (RESOURCE_LOCATIONS.includes(locationSlug)) return 'resources';

  // Мастерская?
  if (WORKSHOP_TO_PARENT_MAP[locationSlug]) return 'workshop';

  // Локации со своей первой вкладкой (не выводятся из tradeConfig)
  if (locationSlug === '1.27.trade-hall') return 'tents';
  if (locationSlug === '1.26.pawn-shop') return 'buyout';

  // Если локация не входит в TRADE_LOCATIONS или WORKSHOP_LOCATIONS – не выбираем вкладку
  if (!isTradeLocation(locationSlug)) return null;

  // Торговые локации
  const config = getTradeLocationConfig(locationSlug);
  if (config?.isProduction) return 'licenses';

  return 'shops';
};