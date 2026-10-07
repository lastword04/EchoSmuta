import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useRefreshCurrentView } from '../../../shared/hooks/location/useRefreshCurrentView';
import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { useGetMyPanelsQuery } from '../../../entities/character/api/panelApi';
import { characterStatsApi } from '../../../entities/character/api/characterStatsApi';
import { economyApi } from '../../../entities/economy/api/economyApi';
import { clearActiveCharacterId } from '../../../shared/store/activeCharacterIdSlice';
import { removeActiveTab } from '../../../shared/store/activeTabSlice';
import { useQuitMutation } from '../../../entities/auth/api/authGameApi';
import { menuItems } from '../../../shared/config/ui/menuItems';
import { useMediaQuery } from '../../../shared/hooks/ui/useMediaQuery';
import { useLocationTopBarState } from '../hooks/useLocationTopBarState';
import visitService from '../../../shared/services/visitService';
import { clearLastMining } from '../../../entities/resources/store/miningSlice';

/**
 * Хук для TopBar: вся логика управления состоянием, обработчики, данные.
 * TopBar компонент становится чистой презентацией.
 */
export const useTopBar = (character, city, onRefresh, isRefreshing, hasUnreadMail, onMailClick) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [quit] = useQuitMutation();
  
  // ── State ──
  const [fontSize, setFontSize] = useState('1.8rem');
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const [isMailLoading, setIsMailLoading] = useState(false);
  const [localRefreshing, setLocalRefreshing] = useState(false);
  
  // ── Refs ──
  const cityNameRef = useRef(null);  

    // ── Redux / RTK Query selectors ──  
  const { data: panelData } = useGetMyPanelsQuery();
  
  // Оборачиваем в useMemo, чтобы объект не пересоздавался при каждом рендере
  const selectedItems = useMemo(() => ({
    first_item: panelData?.first_item || null,
    second_item: panelData?.second_item || null
  }), [panelData?.first_item, panelData?.second_item]);
  
  
  // ── Hooks ──
  const isMobile = useMediaQuery('(max-width: 950px)');
  const { buttons: locationButtons, activeView, showSecondBar } = useLocationTopBarState(character?.location_slug);
  const refreshCurrentView = useRefreshCurrentView(character?.location_slug, character?.id, inventoryApi);
  
  // ── Effects ──
  
  
  // Расчёт fontSize для города
  useEffect(() => {
    if (character?.location_slug && cityNameRef.current && !isMobile && city) {
      const len = city.length;
      if (len <= 6) setFontSize('1.8rem');
      else if (len <= 12) setFontSize('1.6rem');
      else if (len <= 18) setFontSize('1.4rem');
      else setFontSize('1.2rem');
    }
  }, [character?.location_slug, isMobile, city]);
  
  // Закрытие мобильного меню при смене локации
  useEffect(() => {
    setShowMobileMenu(false);
  }, [character?.location_slug]);
  
  // ── Memoized values ──
  const selectedMenuItems = useMemo(() => {
    const ids = [selectedItems.first_item, selectedItems.second_item].filter(Boolean);
    return ids.map(id => menuItems.find(item => item.id === id)).filter(Boolean);
  }, [selectedItems]);
  
  // ── Handlers ──
  const handleExit = useCallback(async () => {
    if (isExiting) return;
    setIsExiting(true);
    
    // Сигналим всем WebSocket'ам что выходим
    window.dispatchEvent(new CustomEvent('game-exiting'));
    
    try {
      if (character?.id) {
        const fingerprint = await visitService.getFingerprint();
        await quit({ characterId: character.id, data: { fingerprint } }).unwrap();
      }
      
      // СНАЧАЛА очищаем activeCharacterId (чтобы skip=true у queries)
      dispatch(clearActiveCharacterId());
      
      
      // ПОТОМ сбрасываем кэш RTK Query
      dispatch(inventoryApi.util.resetApiState());
      dispatch(characterApi.util.resetApiState());
      dispatch(characterStatsApi.util.resetApiState());
      dispatch(economyApi.util.resetApiState());
      dispatch(removeActiveTab());
      dispatch(clearLastMining());
      
      navigate('/characters');
    } catch (error) {
      console.error('Ошибка при выходе:', error);
      navigate('/characters');
    }
  }, [isExiting, character?.id, dispatch, navigate, quit]);
  
  const handleRefresh = useCallback(async () => {
    if (localRefreshing) return;
    setLocalRefreshing(true);
    
    try {
      // Каноничный путь: перекачка данных активной вкладки через реестр viewPrefetches
      await refreshCurrentView();
      if (onRefresh) await onRefresh();
    } finally {
      setLocalRefreshing(false);
    }
  }, [localRefreshing, onRefresh, refreshCurrentView]);

  
  const handleMailClick = useCallback(async () => {
    if (isMailLoading || !onMailClick) return;
    setIsMailLoading(true);
    try {
      await onMailClick();
    } finally {
      setIsMailLoading(false);
    }
  }, [isMailLoading, onMailClick]);
  
  const handlePanelIconClick = useCallback((menuItem, onMenuItemClick) => {
    if (!onMenuItemClick) return;
    
    if (menuItem.location_slug === character?.location_slug) {
      if (onRefresh && !isRefreshing) onRefresh();
      return;
    }
    
    onMenuItemClick(menuItem);
  }, [character?.location_slug, onRefresh, isRefreshing]);
  
  const handleMenuButtonClick = useCallback(() => {
    setShowMobileMenu(prev => !prev);
  }, []);
  
  // ── Return ──
  return {
    // State
    fontSize,
    showMobileMenu,
    isExiting,
    isMailLoading,
    isMobile,
    localRefreshing,
    
    // Refs
    cityNameRef,
    
    // Data
    selectedMenuItems,
    locationButtons,
    activeView,
    showSecondBar,
    
    // Handlers
    handleExit,
    handleRefresh,
    handleMailClick,
    handlePanelIconClick,
    handleMenuButtonClick,
  };
};