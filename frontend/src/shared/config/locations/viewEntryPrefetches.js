import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { captchaApi } from '../../../entities/captcha/api/captchaApi';
import { resourcesApi } from '../../../entities/resources/api/resourcesApi';
import { economyApi } from '../../../entities/economy/api/economyApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { tavernApi } from '../../../entities/economy/api/tavernApi';
import { restApi } from '../../../entities/character/api/restApi';
import { housesApi } from '../../../entities/character/api/housesApi';
import { AVALON_NUMBER } from './locations';
import { getBaseLocationConfig, normalizeViewId } from './locationNavConfig';
import { getTradeLocationConfig } from './tradeConfig';

/**
 * Реестр данных вкладок для useViewEntryPrefetches: какие RTK-запросы кормят вкладку.
 * ⚠️ args должны ПОБАЙТОВО совпадать с аргументами useXxxQuery в компоненте вкладки.
 * Пустой список = вкладка переключается мгновенно.
 *
 * refreshBy (используется useRefreshCurrentView, гейт игнорирует):
 *   'forceRefetch' (по умолчанию) — перекачать зашитые args. Годится для вкладок,
 *   где пользователь не меняет аргументы запроса.
 *   'tags' — инвалидировать теги вместо точечной перекачки. Для вкладок, где
 *   пользователь выбирает фильтры/страницу: перечитается ЯЧЕЙКА, которую
 *   реально смотрят (это делает сам RTK по подписке), а не дефолтная.
 */
export const getViewEntryPrefetches = (locationSlug, viewId, characterId) => {
    if (!locationSlug || !characterId) return [];

    // Неторговые страницы без вкладок: viewId = null, switch не сработает.
    // Кнопка «Обновить» (useRefreshCurrentView) и гейт должны обслуживаться здесь.
    if (locationSlug === `${AVALON_NUMBER}.10.hospital`) {
        return [
            { api: characterApi, endpoint: 'getAppliedSkills', args: undefined },
        ];
    }
    if (locationSlug === `${AVALON_NUMBER}.15.tavern`) {
        return [
            { api: tavernApi, endpoint: 'getMeals', args: undefined },
            { api: characterApi, endpoint: 'getOnlyMe', args: undefined },
        ];
    }
    if (locationSlug === `${AVALON_NUMBER}.12.inn`) {
        return [
            { api: restApi, endpoint: 'getRestStatus', args: undefined },
        ];
    }
    if (locationSlug === `${AVALON_NUMBER}.19.residential-area`) {
        return [
            { api: housesApi, endpoint: 'getHousesStatus', args: undefined },
        ];
    }

    const baseConfig = getBaseLocationConfig(locationSlug);
    const parentSlug = baseConfig.parentSlug || locationSlug;

    switch (normalizeViewId(viewId)) {
        case 'your-shop':
        case 'your-tent':
            // MyShopView: useGetItemsFromLocationQuery(parentLocationSlug)
            return [
                { api: inventoryApi, endpoint: 'getItemsFromLocation', args: parentSlug },
            ];

        case 'shops':
        case 'tents':
            // ShopsListView: первый рендер всегда с дефолтными page/pageSize (стейт сбрасывается).
            // refreshBy: 'tags' — кнопка «Обновить» перечитает открытый поиск (itemName/itemKind/page),
            // т.к. getShopsList ставит тег только по locationSlug, без фильтров
            return [
                { api: inventoryApi, endpoint: 'getShopsList', args: { locationSlug: parentSlug, page: 1, pageSize: 5 }, refreshBy: 'tags', tagType: 'ShopsList' },
            ];

        case 'licenses':
            if (baseConfig.isProduction) {
                // ProductionLicenseView: useGetCraftingLicenseStatusQuery({ locationSlug, characterId })
                return [
                    { api: inventoryApi, endpoint: 'getCraftingLicenseStatus', args: { locationSlug: parentSlug, characterId } },
                ];
            }
            // LicenseViewContainer: useGetCityShopQuery({ locationSlug, characterId })
            return [
                { api: inventoryApi, endpoint: 'getCityShop', args: { locationSlug: parentSlug, characterId } },
            ];

        case 'recipes': {
            // RecipesView: дефолтный selectedQuantity = quantityOptions[0], совпадает при первом рендере.
            // refreshBy: 'tags' — кнопка «Обновить» перечитает ВЫБРАННЫЙ пользователем quantity
            const quantity = getTradeLocationConfig(parentSlug)?.quantityOptions?.[0] ?? 1;
            return [
                { api: inventoryApi, endpoint: 'getRecipes', args: { quantity, locationSlug: parentSlug }, refreshBy: 'tags', tagType: 'Recipes' },
            ];
        }

        case 'your-recipes':
            // MyRecipesView: useGetMyRecipesQuery({ locationSlug })
            return [
                { api: inventoryApi, endpoint: 'getMyRecipes', args: { locationSlug: parentSlug } },
            ];

        case 'sales-history':
            // SalesHistoryView: useGetSalesHistoryQuery({ limit: 30, locationSlug })
            return [
                { api: inventoryApi, endpoint: 'getSalesHistory', args: { limit: 30, locationSlug: parentSlug } },
            ];

        case 'workshop':
            // useWorkshopLogic: useGetStartedCraftingQuery / getStockRecipes / getCityShopStats (все с parentLocationSlug)
            // + капча: query теперь, гейт дожидается её → вход в мастерскую атомарный
            return [
                { api: inventoryApi, endpoint: 'getStartedCrafting', args: parentSlug },
                { api: inventoryApi, endpoint: 'getStockRecipes', args: parentSlug },
                { api: inventoryApi, endpoint: 'getCityShopStats', args: parentSlug },
                { api: inventoryApi, endpoint: 'getCraftingStatus', args: undefined },
                { api: captchaApi, endpoint: 'getCaptcha', args: undefined },
            ];

        case 'deals':
            // useDealsLogic: пять запросов; все они же — optional-префетч при входе в палатку,
            // поэтому к моменту клика кэш обычно горячий и гейт проходит мгновенно
            return [
                { api: inventoryApi, endpoint: 'getNearbyPartners', args: locationSlug },
                { api: inventoryApi, endpoint: 'getTradeLicenseStatus', args: { characterId } },
                { api: inventoryApi, endpoint: 'getCharacterItems', args: undefined },
                { api: inventoryApi, endpoint: 'getMyEquipment', args: undefined },
                { api: resourcesApi, endpoint: 'getMyResources', args: undefined },
            ];

        case 'buyout':
        case 'exchange':
            // PawnShopPage (Скупка и Биржа): useGetResourcesQuery(undefined) / useGetLotsQuery(undefined)
            return [
                { api: economyApi, endpoint: 'getResources', args: undefined },
                { api: economyApi, endpoint: 'getLots', args: undefined },
            ];

        case 'resources':
            // ResourcePage / useMiningLogic: useGetResourcesQuery(locationSlug),
            // getMiningStatus.initiate(undefined), useGetCaptchaQuery(undefined)
            return [
                { api: resourcesApi, endpoint: 'getResources', args: locationSlug },
                { api: resourcesApi, endpoint: 'getMiningStatus', args: undefined },
                { api: captchaApi, endpoint: 'getCaptcha', args: undefined },
            ];

        default:
            return [];
    }
};