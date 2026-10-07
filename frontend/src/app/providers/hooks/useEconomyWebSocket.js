import { useEffect, useRef } from 'react';
import { getBaseEconomyInvalidationTags, getEconomyResyncInvalidationTags } from '../../../shared/config/websocketEvents/invalidateOnEconomyEvent';
import { useDispatch, useSelector } from 'react-redux';
import { getBaseLocationConfig } from '../../../shared/config/locations/locationNavConfig'; 
import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { economyApi } from '../../../entities/economy/api/economyApi';
import { resourcesApi } from '../../../entities/resources/api/resourcesApi';
import { housesApi } from '../../../entities/character/api/housesApi';
import { chatApi } from '../../../entities/chat/api/chatApi';
import { commitCharacterFields, commitChatRoom } from '../../../entities/character/store/characterSlice';
import { setHouseOverride, clearHouseOverride } from '../../../entities/character/store/houseUiSlice';
import { moveOnlineUser, ONLINE_PAGE_LIMIT, ONLINE_PAGE_OFFSET } from '../../../app/providers/lib/onlineCacheSync';
import { storeRef } from '../../../shared/store/storeRef';

export const useEconomyWebSocket = (character) => {
  const dispatch = useDispatch();
  
  const locationFromRedux = useSelector((state) => state.local?.locationSlug || state.character?.location_slug);
  const currentLocationSlug = character?.location_slug || locationFromRedux;

  // Ref на character: обработчик house-updated создаётся один раз (deps: [dispatch]),
  // но должен видеть актуального персонажа. Прямая зависимость от character
  // пересоздавала бы listener на каждый WS-тик.
  const characterRef = useRef(character);
  useEffect(() => {
    characterRef.current = character;
  }, [character]);
  

  useEffect(() => {    
    const handleEconomyUpdate = (event) => {      
      const detail = event.detail || {};
      const action = detail.action;        

      // 1. БАЗОВАЯ ИНВАЛИДАЦИЯ
      const baseTags = getBaseEconomyInvalidationTags();
      dispatch(characterApi.util.invalidateTags(baseTags.characterApi));
      dispatch(economyApi.util.invalidateTags(baseTags.economyApi));
      dispatch(resourcesApi.util.invalidateTags(baseTags.resourcesApi));
      dispatch(inventoryApi.util.invalidateTags(baseTags.inventoryApi));

      // 2. ТОЧЕЧНАЯ ИНВАЛИДАЦИЯ ДЛЯ ТОРГОВЛИ
      if (action === 'deal_completed' ||
          action === 'lot_created' || action === 'lot_sold' || action === 'lot_cancelled' ||
          action === 'sale_item_created' || action === 'sale_item_removed' || 
          action === 'sale_price_updated' || action === 'shop_item_added' || 
          action === 'shop_item_removed' || 
          action === 'shop_info_updated' || action === 'shop_photo_updated' ) {

        const shopId = detail.shop_id;
        const eventLocationSlug = detail.location_slug;
        
          const tagsToInvalidate = [
          { type: 'Inventory' },
          { type: 'Resources' },
          { type: 'Lots' }
        ];

        if (shopId) {
          tagsToInvalidate.push({ type: 'CityShop', id: shopId });
          tagsToInvalidate.push({ type: 'ShopItems', id: shopId });
        }
        
        if (eventLocationSlug) {
          // Инвалидируем и eventLocationSlug, и его parentSlug (если они отличаются)
          const baseConfig = getBaseLocationConfig(eventLocationSlug);
          const parentSlug = baseConfig?.parentSlug || eventLocationSlug;
          const slugs = new Set([eventLocationSlug, parentSlug]);

          slugs.forEach(slug => {
            tagsToInvalidate.push({ type: 'ShopsList', id: slug });
            tagsToInvalidate.push({ type: 'ShopItems', id: slug });
            tagsToInvalidate.push({ type: 'CityShop', id: slug });
            tagsToInvalidate.push({ type: 'CraftingLicense', id: slug });
            tagsToInvalidate.push({ type: 'StartedCrafting', id: slug });
            tagsToInvalidate.push({ type: 'WorkshopStats', id: slug });
            tagsToInvalidate.push({ type: 'SalesHistory', id: slug });
          });
        } else {
          tagsToInvalidate.push('ShopsList');
          tagsToInvalidate.push('CityShop');
          tagsToInvalidate.push('CraftingLicense');
        }           
        
        dispatch(inventoryApi.util.invalidateTags(tagsToInvalidate));
      }
      
    };

    window.addEventListener('economy-updated', handleEconomyUpdate);

    return () => {
      window.removeEventListener('economy-updated', handleEconomyUpdate);
    };
  }, [dispatch, currentLocationSlug]);

  // ═══ ДОМА: реакция на события house-updated ═══
  // Инвалидация — всегда (дома/мебель/гости могли измениться для всех).
  // Персональный переход — только если событие про меня:
  //   affected_character_id === мой id. Тогда мы сами переключаем current_house_id,
  //   chatRoomId и кэши онлайна — без ожидания refetch, чтобы UI не отставал.
  useEffect(() => {
    const handleHouseUpdate = (event) => {
      const detail = event.detail || {};
      const { action, house_id, affected_character_id } = detail;
      const me = characterRef.current;

      // Инвалидация для всех подписчиков дома.
      // HousesGuests НЕ инвалидируем при guest_left про самого себя:
      // собственный выход обрабатывается через commitLocation (handleLocationChange)
      // или handleExit, которые сами делают refetch. Иначе refetch вернет пустой
      // список до смены локации, и будет мелькание "Гости (0/10)".
      const shouldInvalidateGuests = !(action === 'guest_left' && affected_character_id === me?.id);
      const tagsToInvalidate = ['Houses', 'HouseFurniture'];
      if (shouldInvalidateGuests) {
        tagsToInvalidate.push('HousesGuests');
      }
      dispatch(housesApi.util.invalidateTags(tagsToInvalidate));

      const RESET_ACTIONS = ['furniture_changed', 'wallpaper_changed', 'guest_left', 'guest_kicked'];
      if (RESET_ACTIONS.includes(action) && affected_character_id !== me.id) {
        dispatch(clearHouseOverride());
      }

      // Оптимистичное удаление из кэша — только для ЧУЖИХ персонажей.
      // Для себя не нужно: собственный выход обрабатывается авторитетно
      // (handleExit / commitLocation). Иначе при переходе в другую локацию
      // кэш гостей опустеет раньше, чем commitLocation переключит страницу.
      if ((action === 'guest_left' || action === 'guest_kicked') && affected_character_id && affected_character_id !== me.id) {
        dispatch(housesApi.util.updateQueryData('getHousesStatus', me.id, (draft) => {
          if (!draft) return;
          const drop = (list) => (list || []).filter(g => g.character_id !== affected_character_id);
          if (draft.current_house) {
            draft.current_house.guests = drop(draft.current_house.guests);
            draft.current_house.guests_count = draft.current_house.guests.length;
          }
          (draft.houses || []).forEach(h => {
            h.guests = drop(h.guests);
            h.guests_count = (h.guests || []).length;
          });
        }));
        dispatch(housesApi.util.updateQueryData('getHouseGuests', house_id, (draft) => {
          if (!draft) return;
          draft.guests = (draft.guests || []).filter(g => g.character_id !== affected_character_id);
        }));
      }

      // Персональная реакция — только для меня.
      if (!me || affected_character_id !== me.id) return;

      const globalState = chatApi.endpoints.getOnlineCharacters.select({
        locationSlug: null, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET,
      })(storeRef.current.getState());
      const userObject = globalState?.data?.objects?.find(u => u.id === me.id);

      if (action === 'guest_accepted') {
        // Меня приняли в дом: переезжаем внутрь.
        const newRoom = `house:${house_id}`;
        
        if (detail.house_payload) {
          dispatch(setHouseOverride(detail.house_payload));
        }

        if (userObject) {
          moveOnlineUser(dispatch, {
            characterId: me.id,
            oldLocationSlug: me.location_slug,
            newLocationSlug: newRoom,
            userData: userObject,
          });
        }
        dispatch(commitCharacterFields({ current_house_id: house_id }));
        dispatch(commitChatRoom(newRoom));
        dispatch(chatApi.endpoints.getOnlineCharacters.initiate(
          { roomId: newRoom, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
          { forceRefetch: true, subscribe: false }
        )).catch(() => null);
      }

      if (action === 'guest_kicked') {
        // Меня выгнали: возвращаемся на улицу текущей локации.
        const backLocation = me.location_slug;
        dispatch(clearHouseOverride());
        if (userObject) {
          moveOnlineUser(dispatch, {
            characterId: me.id,
            oldLocationSlug: `house:${house_id}`,
            newLocationSlug: backLocation,
            userData: userObject,
          });
        }
        dispatch(commitCharacterFields({ current_house_id: null }));
        dispatch(commitChatRoom(backLocation));
        dispatch(chatApi.endpoints.getOnlineCharacters.initiate(
          { roomId: backLocation, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
          { forceRefetch: true, subscribe: false }
        )).catch(() => null);
      }

      // guest_left: собственного действия не требуем. Если я вышел сам — я уже
      // всё сделал локально; если меня оффлайн-выкинули — меня нет в сети;
      // если владелец ушёл — это не про меня. Инвалидация выше сработает.
    };

    window.addEventListener('house-updated', handleHouseUpdate);
    return () => window.removeEventListener('house-updated', handleHouseUpdate);
  }, [dispatch]);
  

  // ═══ РЕСИНК ПОСЛЕ ОБРЫВА WS ═══
  // События, ушедшие в обрыв, потеряны навсегда (pub/sub без истории) —
  // состав пакета не зависит от того, что именно пропустили.
  // Инвалидация дешёвая (пометка stale), перечитают только смонтированные.
  useEffect(() => {
    const handleResync = () => {
      const resyncTags = getEconomyResyncInvalidationTags();
      dispatch(characterApi.util.invalidateTags(resyncTags.characterApi));
      dispatch(economyApi.util.invalidateTags(resyncTags.economyApi));
      dispatch(resourcesApi.util.invalidateTags(resyncTags.resourcesApi));
      dispatch(inventoryApi.util.invalidateTags(resyncTags.inventoryApi));
      dispatch(chatApi.util.invalidateTags(resyncTags.chatApi));
    };

    window.addEventListener('economy-resync', handleResync);
    return () => window.removeEventListener('economy-resync', handleResync);
  }, [dispatch]);
};