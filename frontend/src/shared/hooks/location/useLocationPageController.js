import { useEffect, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';

import { useLocationNavigation } from './useLocationNavigation';
import { getInitialView, normalizeViewId } from '../../../shared/config/locations/locationNavConfig';
import { useViewEntryPrefetches } from './useViewEntryPrefetches';
import { consumeAction } from '../../store/topBarActionsSlice';
import { useRefreshCurrentView } from './useRefreshCurrentView';

/**
 * Контроллер для ПРОСТЫХ торговых локаций (TradeHall, PawnShop).
 * 
 * НЕ подходит для:
 * - Локаций с физической сменой location_slug при переключении вкладок (аптека → лаборатория)
 * - Локаций со сложной суб-навигацией (CityTradeLocation)
 * 
 * Для таких случаев используйте кастомную логику + прямую подписку на topBarActionsSlice.
 *
 * 
 * @param {object} character - текущий персонаж
 * @returns {object} { activeTab } - нормализованная активная вкладка
 */
export const useLocationPageController = (character, onViewChange) => {
  const dispatch = useDispatch();
  const lastAction = useSelector(state => state.topBarActions?.lastAction);
  const { navigation } = useLocationNavigation();
  const { requestView } = useViewEntryPrefetches(character?.location_slug, character?.id);
  const refreshCurrentView = useRefreshCurrentView(character?.location_slug, character?.id);
  
  const activeTab = useMemo(() => {
    const fromNav = navigation?.activeView ? normalizeViewId(navigation.activeView) : null;
    return fromNav || getInitialView(character?.location_slug);
  }, [navigation?.activeView, character?.location_slug]);
  
  // Обработка команд от TopBar
  useEffect(() => {
    if (!lastAction || lastAction.consumed) return;
    
    const { type, payload } = lastAction;
    
    if (type === 'TRADE_BUTTON_CLICK') {
      // Команда для другой локации — игнорируем
      if (payload.locationSlug !== character?.location_slug) {
        dispatch(consumeAction());
        return;
      }
      
      const targetId = normalizeViewId(payload.id);
      
      if (targetId === activeTab) {
        // Клик на ту же вкладку — обновление данных активной вкладки
        refreshCurrentView();
      } else if (onViewChange) {
        // Кастомная логика переключения (например, changeLocation для мастерских)
        onViewChange(targetId);
      } else {
        // Переключение вкладки
        requestView(targetId);
      }
      
      dispatch(consumeAction());
    }
  }, [lastAction, character?.location_slug, activeTab, onViewChange, requestView, refreshCurrentView, dispatch]);
  
  return { activeTab };
};