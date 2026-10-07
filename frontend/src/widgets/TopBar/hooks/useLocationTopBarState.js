import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { getBaseLocationConfig, normalizeViewId, getInitialView } from '../../../shared/config/locations/locationNavConfig';
import { useShopStatus } from '../../../entities/items/hooks/useShopStatus';

export const useLocationTopBarState = (locationSlug) => {
  const navigation = useSelector(state => state.locationNavigation);
  const baseConfig = useMemo(() => getBaseLocationConfig(locationSlug), [locationSlug]);

  const { hasShop: shopStatus } = useShopStatus(locationSlug);

  const isCurrentlyInWorkshop = baseConfig.isWorkshop;
  const hasShopLoaded = shopStatus !== null || isCurrentlyInWorkshop;
  const hasShop = (shopStatus ?? false) || isCurrentlyInWorkshop;

  // Активная вкладка — из контроллера; fallback (F5) — дефолт из конфига
  const activeView = useMemo(() => {
    const fromNav = navigation?.activeView ? normalizeViewId(navigation.activeView) : null;
    if (fromNav) {
      if (fromNav === 'recipes' || fromNav === 'your-recipes' || fromNav === 'sales-history') return 'licenses';
      return fromNav;
    }
    return getInitialView(locationSlug);
  }, [navigation?.activeView, locationSlug]);

  const finalButtons = useMemo(() => {
    const filtered = baseConfig.buttons.filter(button => {
      const isWorkshopBtn = button.id === 'workshop';
      const isYourShopBtn = button.id.includes('your-');

      if (!hasShopLoaded) {
        if (isYourShopBtn || isWorkshopBtn) return false;
      } else {
        if ((isYourShopBtn || isWorkshopBtn) && !hasShop) return false;
      }
      return true;
    });

    const workshopButtonExists = filtered.some(b => b.id === 'workshop');
    const shouldShowDynamicWorkshop =
      !workshopButtonExists &&
      (activeView === "your-shop" || activeView === "workshop") &&
      baseConfig.navLabels?.workshop &&
      hasShop &&
      hasShopLoaded;

    if (shouldShowDynamicWorkshop) {
      filtered.push({
        id: 'workshop',
        label: baseConfig.navLabels.workshop
      });
    }

    return filtered;
  }, [baseConfig.buttons, baseConfig.navLabels, hasShop, hasShopLoaded, activeView]);

  return {
    buttons: finalButtons,
    activeView,
    showSecondBar: finalButtons.length > 0,
    parentSlug: baseConfig.parentSlug
  };
};