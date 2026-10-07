import { useSelector } from 'react-redux';
import { getBaseLocationConfig } from '../../../shared/config/locations/locationNavConfig';
import {
  useGetCityShopQuery,
  useGetCraftingLicenseStatusQuery,
} from '../api/inventoryApi';

/**
 * Единый источник правды «есть ли лавка / действующая лицензия» для локации.
 * Возвращает { hasShop: null | true | false }, где null = «ещё грузится или ошибка».
 * Заменяет Redux shopStatusSlice (multi-writer) на RTK Query (один кэш, дедупликация).
 */
export const useShopStatus = (locationSlug) => {
  const characterId = useSelector(state => state.local.activeCharacterId);
  const baseConfig = getBaseLocationConfig(locationSlug);
  const { parentSlug, isProduction, isWorkshop } = baseConfig;

  const hasYourButton = baseConfig.buttons.some(b => b.id.includes('your-'));

  const cityShop = useGetCityShopQuery(
    { locationSlug: parentSlug, characterId },
    { skip: !characterId || isWorkshop || isProduction || !hasYourButton }
  );

  const license = useGetCraftingLicenseStatusQuery(
    { locationSlug, characterId },
    { skip: !characterId || isWorkshop || !isProduction }
  );

  // Статус ошибки: 404 = «лавки нет» (это ответ), прочее = сбой (не знаем → null)
  const errStatus = (q) => q.error?.status ?? q.error?.response?.status;
  const shop404 = cityShop.isError && errStatus(cityShop) === 404;
  const shopFail = cityShop.isError && !shop404;
  const lic404 = license.isError && errStatus(license) === 404;
  const licFail = license.isError && !lic404;

  // Мастерская: лавка есть по определению
  if (isWorkshop) return { hasShop: true };

  // Production: статус = действующая лицензия
  if (isProduction) {
    if (lic404) return { hasShop: false };
    if (licFail || license.currentData === undefined) return { hasShop: null };
    return { hasShop: !!license.currentData?.is_active };
  }

  // Торговая: статус = наличие лавки
  if (hasYourButton) {
    if (shop404) return { hasShop: false };
    if (shopFail || cityShop.currentData === undefined) return { hasShop: null };
    return { hasShop: !!cityShop.currentData };
  }

  return { hasShop: false };
};