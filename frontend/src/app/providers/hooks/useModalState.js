import { useState, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { characterApi } from '../../../entities/character/api/characterApi';
import { mailApi } from '../../../entities/mail/api/mailApi';
import { inventoryApi } from '../../../entities/items/api/inventoryApi';

/**
 * Домен модалок: единый activeModal (один источник правды),
 * статистика карты, друзья (doNotReceive).
 */
export const useModalState = (navigate) => {
  const dispatch = useDispatch();
  const [activeModal, setActiveModal] = useState(null);
  const [doNotReceive, setDoNotReceive] = useState(false);

  // Статистика карты: стартовый кэш + presence-инкременты (usePresenceSync) +
  // инвалидация в economy-ресинке. Поллинг убран: он задерживал обновление
  // счётчиков после реконнекта до 30 сек, конфликтуя с событийной моделью.
  const { data: locationStatsData } = characterApi.endpoints.getLocationsStats.useQuery(undefined);

  // Преобразуем массив в объект { location_slug: count }
  const locationCounts = useMemo(() => {
    if (!locationStatsData) return {};  // ← Пустой объект вместо null — защита от краша
    const countMap = {};
    locationStatsData.forEach(item => {
      countMap[item.location_slug] = item.count;
    });
    return countMap;
  }, [locationStatsData]);

  const handleOpenFriends = async () => {
    try {
      const data = await dispatch(mailApi.endpoints.getMailSettings.initiate()).unwrap();
      setDoNotReceive(!!data?.is_block_send_mails);
    } catch (error) {
      console.error('Ошибка загрузки настроек почты:', error);
    }
    setActiveModal('FRIENDS_MODAL');
  };

  const handleOpenInventory = async () => {
    try {
      await Promise.all([
        dispatch(inventoryApi.endpoints.getMyEquipment.initiate()).unwrap(),
        dispatch(inventoryApi.endpoints.getCharacterItems.initiate()).unwrap(),
      ]);
    } catch (error) {
      console.error('Ошибка загрузки инвентаря:', error);
    }
    setActiveModal('INVENTORY_MODAL');
  };

  const handleOpenMagic = async () => {
    try {
      await dispatch(inventoryApi.endpoints.getCharacterItems.initiate()).unwrap();
    } catch (error) {
      console.error('Ошибка загрузки магии:', error);
    }
    setActiveModal('MAGIC_MODAL');
  };

  const handleMenuItemClick = async (menuItem) => {
    if (menuItem.modalType === 'MAP_MODAL') {
      // Данные уже в кэше — просто открываем модалку
      setActiveModal('MAP_MODAL');
      return;
    }
    if (menuItem.modalType === 'FRIENDS_MODAL') {
      await handleOpenFriends();
      return;
    }
    if (menuItem.modalType === 'INVENTORY_MODAL') {
      await handleOpenInventory();
      return;
    }
    if (menuItem.modalType === 'MAGIC_MODAL') {
      await handleOpenMagic();
      return;
    }
    if (menuItem.modalType === 'CABINET_MODAL') {
      navigate('/characters');
      return;
    }
    setActiveModal(menuItem.modalType);
  };

  return {
    activeModal,
    setActiveModal,
    locationCounts,
    doNotReceive,
    setDoNotReceive,
    handleMenuItemClick,
    handleOpenFriends,
    handleOpenMagic,
  };
};