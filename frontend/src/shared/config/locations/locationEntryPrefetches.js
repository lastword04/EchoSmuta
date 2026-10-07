import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { captchaApi } from '../../../entities/captcha/api/captchaApi';
import { resourcesApi } from '../../../entities/resources/api/resourcesApi';
import { economyApi } from '../../../entities/economy/api/economyApi';
import { tavernApi } from '../../../entities/economy/api/tavernApi';
import { restApi } from '../../../entities/character/api/restApi';
import { housesApi } from '../../../entities/character/api/housesApi';
import { characterApi } from '../../../entities/character/api/characterApi'; 
import { AVALON_NUMBER } from './locations'; 

import { getInitialView, getBaseLocationConfig } from './locationNavConfig';

/**
 * Единая карта префетчей для дефолтной вкладки локации.
 * Используется в handleLocationChange (переходы) для инвалидации и forceRefetch.
 *
 * Чат-префетчи НЕ включены — они обрабатываются отдельно в useAtomicPageReady
 * и useLocationTransition для гарантии атомарности F5 и переходов.
 *
 * required: true  — Boot Gate ждёт перед скрытием overlay (атомарность F5)
 * required: false — префетчится для ускорения соседних вкладок, но не блокирует overlay
 */

export const getLocationEntryPrefetches = (locationSlug, characterId) => {
    if (!locationSlug || !characterId) return [];


    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // УРОВЕНЬ 1: Базовые префетчи специфичных локаций
    // (Не зависят от вкладок, нужны для Boot Gate / атомарности F5)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if (locationSlug === `${AVALON_NUMBER}.10.hospital`) {
        return [
            { api: characterApi, endpoint: 'getAppliedSkills', args: undefined, required: true }
        ];
    }
    if (locationSlug === `${AVALON_NUMBER}.15.tavern`) {
        return [
            { api: tavernApi, endpoint: 'getMeals', args: undefined, required: true }
        ];
    }
    if (locationSlug === `${AVALON_NUMBER}.12.inn`) {
        return [
            { api: restApi, endpoint: 'getRestStatus', args: undefined, required: true, alwaysFresh: true }
        ];
    }
    if (locationSlug === `${AVALON_NUMBER}.19.residential-area`) {
        return [
            { api: housesApi, endpoint: 'getHousesStatus', args: characterId, required: true, alwaysFresh: true }
        ];
    }


    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // УРОВЕНЬ 2: Префетчи дефолтных вкладок (Торговля, Ресурсы и т.д.)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    const baseConfig = getBaseLocationConfig(locationSlug);
    const parentSlug = baseConfig.parentSlug || locationSlug;
    const defaultView = getInitialView(locationSlug);

    switch (defaultView) {
        case 'shops':
            return [
                { api: inventoryApi, endpoint: 'getShopsList', args: { locationSlug: parentSlug, page: 1, pageSize: 5 }, required: true },
                { api: inventoryApi, endpoint: 'getCityShop', args: { locationSlug: parentSlug, characterId }, required: true },
            ];

        case 'licenses':
            return [
                { api: inventoryApi, endpoint: 'getCraftingLicenseStatus', args: { locationSlug: parentSlug, characterId }, required: true },
            ];

        case 'workshop':
            return [
                { api: inventoryApi, endpoint: 'getCraftingStatus', args: undefined, required: true },
                baseConfig.isProduction
                    ? { api: inventoryApi, endpoint: 'getCraftingLicenseStatus', args: { locationSlug: parentSlug, characterId }, required: true }
                    : { api: inventoryApi, endpoint: 'getCityShop', args: { locationSlug: parentSlug, characterId }, required: true },
                // required: true — иначе WorkshopView монтируется до их готовности
                // и рисует null-кадры (isInitialDataLoading). Гейтит и переход, и F5.
                { api: inventoryApi, endpoint: 'getStartedCrafting', args: parentSlug, required: true },
                { api: inventoryApi, endpoint: 'getStockRecipes', args: parentSlug, required: true },
                { api: inventoryApi, endpoint: 'getCityShopStats', args: parentSlug, required: true },
                // Капча: Boot Gate дожидается → атомарный F5/переход в мастерскую
                { api: captchaApi, endpoint: 'getCaptcha', args: undefined, required: true },
            ];

        case 'buyout':
            return [
                { api: economyApi, endpoint: 'getResources', args: undefined, required: true },
                { api: economyApi, endpoint: 'getLots', args: undefined, required: true },
            ];

        case 'tents':
            return [
                { api: inventoryApi, endpoint: 'getShopsList', args: { locationSlug: parentSlug, page: 1, pageSize: 5 }, required: true },
                { api: inventoryApi, endpoint: 'getCityShop', args: { locationSlug: parentSlug, characterId }, required: true },
                { api: inventoryApi, endpoint: 'getSalesHistory', args: { locationSlug: parentSlug, limit: 30 }, required: false },
                { api: inventoryApi, endpoint: 'getNearbyPartners', args: locationSlug, required: false },
                { api: inventoryApi, endpoint: 'getTradeLicenseStatus', args: { characterId }, required: false },
                { api: inventoryApi, endpoint: 'getCharacterItems', args: undefined, required: false },
                { api: inventoryApi, endpoint: 'getMyEquipment', args: undefined, required: false },
                { api: resourcesApi, endpoint: 'getMyResources', args: undefined, required: false },
            ];

        case 'resources':
            return [
                { api: resourcesApi, endpoint: 'getResources', args: locationSlug, required: true },
                { api: resourcesApi, endpoint: 'getMiningStatus', args: undefined, required: true },
                { api: resourcesApi, endpoint: 'getMyResources', args: undefined, required: false },
                // Капча как query (паритет с мастерской): гейт дожидается → атомарный F5/переход.
                { api: captchaApi, endpoint: 'getCaptcha', args: undefined, required: true },
            ];

        default:
            // Неторговые локации — только чат (обрабатывается отдельно)
            return [];
    }
};