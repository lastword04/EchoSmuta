import { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useUploadFileMutation } from '../../../entities/file/api/fileApi';
import { config } from '../../../shared/config/env/env';
import { characterApi } from '../../../entities/character/api/characterApi';
import { chatApi } from '../../../entities/chat/api/chatApi';
import { commitChatRoom, commitCharacterFields } from '../../../entities/character/store/characterSlice';
import { setHouseOverride, clearHouseOverride, patchHouseOverride } from '../../../entities/character/store/houseUiSlice';
import {
  housesApi,
  useGetHousesStatusQuery,
  useBuyHouseMutation,
  useEnterHouseMutation,
  useExitHouseMutation,
  useGetMyFurnitureQuery,  
  useInstallFurnitureMutation,
  useUninstallFurnitureMutation,
  useUpdateHouseWallpaperMutation,
  useKnockHouseMutation,
  useGetHouseGuestsQuery,
  useAcceptGuestRequestMutation,
  useRejectGuestRequestMutation,
  useKickHouseGuestMutation,
} from '../../../entities/character/api/housesApi';
import { moveOnlineUser } from '../../../app/providers/lib/onlineCacheSync';
import { storeRef } from '../../../shared/store/storeRef';
import { useErrorToast } from '../../../shared/hooks/ui/useErrorToast';
import { getErrorMessage } from '../../../shared/lib/error/getErrorMessage';

export const useHouseActions = (character) => {
  const { data: statusData, refetch } = useGetHousesStatusQuery(character?.id, { skip: !character });
  const { data: myFurnitureData } = useGetMyFurnitureQuery(character?.id, { skip: !character });

  const [buyHouse, { isLoading: isBuying }] = useBuyHouseMutation();
  const [enterHouse] = useEnterHouseMutation();
  const [exitHouse, { isLoading: isExiting }] = useExitHouseMutation();
  const [installFurniture] = useInstallFurnitureMutation();
  const [uninstallFurniture] = useUninstallFurnitureMutation();
  const [knockHouse] = useKnockHouseMutation();
  const [acceptGuestRequest] = useAcceptGuestRequestMutation();
  const [rejectGuestRequest] = useRejectGuestRequestMutation();
  const [kickHouseGuest] = useKickHouseGuestMutation();
  const [updateHouseWallpaper, { isLoading: isUpdatingWallpaper }] = useUpdateHouseWallpaperMutation();
  const [uploadFile] = useUploadFileMutation();

  const dispatch = useDispatch();
  const { currentError, showError } = useErrorToast();

  const [activeTab, setActiveTab] = useState('house');
  const [busyItemId, setBusyItemId] = useState(null);
  const [busyHouseId, setBusyHouseId] = useState(null);
  const [busyAcceptId, setBusyAcceptId] = useState(null);
  const [busyRejectId, setBusyRejectId] = useState(null);
  const [busyGuestId, setBusyGuestId] = useState(null);
  const [knockHouseNumber, setKnockHouseNumber] = useState('');
  const [isKnocking, setIsKnocking] = useState(false);
  const [selectedWallpaperFile, setSelectedWallpaperFile] = useState(null);
  const [wallpaperPreviewUrl, setWallpaperPreviewUrl] = useState(null);

  // houseOverride живёт в Redux (houseUi slice): в него пишут и мутации здесь,
  // и WS-событие guest_accepted из useEconomyWebSocket. Один канал → один
  // батч React 18 → атомарный рендер страницы, чата и заголовка.
  const houseOverride = useSelector(state => state.houseUi?.houseOverride ?? null);  
  const houseOverrideId = houseOverride?.id ?? null;

  const isMountedRef = useRef(true);
    useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!houseOverrideId) return;    
    // Проверяем, находимся ли мы все еще в этом доме по ЛЮБОМУ из стабильных индикаторов.
    // Это предотвращает очистку override, если current_house_id временно стал null при рефетче.
    const isStillInThisHouse = 
        character?.current_house_id === houseOverrideId || 
        character?.chat_room_id === `house:${houseOverrideId}`;    
    if (!isStillInThisHouse) {
      dispatch(clearHouseOverride());
    }    
  }, [character?.current_house_id, character?.chat_room_id, houseOverrideId, dispatch]);  

    // Приоритет override → character → chat_room_id.
    // statusData НЕ используется: он отстает при выходе (ждет refetch) и создает рассинхрон.
    const currentHouseId =
        houseOverride?.id
        ?? character?.current_house_id
        ?? (character?.chat_room_id?.startsWith('house:') ? character.chat_room_id.replace('house:', '') : null);
    const isInsideHouse = currentHouseId !== null;
 

  const { currentData: guestsData } = useGetHouseGuestsQuery(
    currentHouseId,
    { skip: !currentHouseId }
  );

   // NOTE: override НЕ управляет guests/guests_count. Они всегда читаются
  // напрямую из guestsData (см. viewedHouse ниже), чтобы «Выгнать» и
  // «Стучится» обновлялись в ОДНОМ рендере, а не разъезжались на кадр.
  // Раньше override перекрывал их, а requests шли из RTK — отсюда задержка.



  // Вход на страницу домов: статус перечитывается с сервера безусловно.
  // Инвалидация тегом не refetch'ит неактивный query, а кэш между
  // кабинета/локациями может быть протухшим (события WS ушли без подписчика).
  useEffect(() => {
    refetch();
  }, [refetch]);

  useEffect(() => {
    return () => {
      if (wallpaperPreviewUrl && wallpaperPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(wallpaperPreviewUrl);
      }
    };
  }, [wallpaperPreviewUrl]);

  useEffect(() => {
    (statusData?.houses || []).forEach(h => {
      if (h.wallpaper_photo_id) {
        const img = new Image();
        img.src = `${config.FILE_API_BASE_URL}/${h.wallpaper_photo_id}/content`;
      }
    });
  }, [statusData?.houses]);

  const houses = statusData?.houses || [];
  const housePrice = statusData?.house_price;
  const maxGuests = statusData?.max_guests || 10;
  const currentHouse = houses.find(h => h.id === currentHouseId);
  const myFurniture = myFurnitureData || [];
  

  // Показываемый дом: свой из списка или чужой из current_house,
  // поверх — свежие данные мутации, если они про этот же дом
  const baseViewedHouse = isInsideHouse ? (currentHouse || statusData?.current_house || null) : null;
  // Приоритет — свежий ответ мутации (enter/install/uninstall):
  // для enter это полный payload, для install/uninstall — частичный.
  // Если base есть и id совпадает — merge; иначе используем override как есть.
  const viewedHouse = (() => {
    if (!isInsideHouse) return null;

    let base = null;
    if (houseOverride) {
        const b = currentHouse || statusData?.current_house;
        base = b && b.id === houseOverride.id ? { ...b, ...houseOverride } : houseOverride;
    } else {
        base = baseViewedHouse;
    }
    if (!base) return null;

    // guests/guests_count — ЕДИНСТВЕННЫЙ источник guestsData. Так «Выгнать»
    // (guests) и «Стучится» (requests) меняются в одном рендере: оба поля
    // приходят из одного RTK-запроса и одного updateQueryData в хендлерах.
    if (guestsData) {
        return {
            ...base,
            guests: guestsData.guests || [],
            guests_count: (guestsData.guests || []).length,
        };
    }
    return base;
  })();

  const isOwner = currentHouse !== undefined || viewedHouse?.is_owner === true;
  const houseFurniture = viewedHouse?.furniture || [];

  const requests = guestsData?.requests || [];

  const handleBuy = async () => {
    try {
      await buyHouse().unwrap();
      dispatch(characterApi.util.invalidateTags(['Character']));
      refetch();
    } catch (e) {
      showError(getErrorMessage(e, 'Ошибка при покупке дома'));
    }
  };

  const handleEnter = async (houseId) => {
    if (busyHouseId !== null) return;
    setBusyHouseId(houseId);
    try {
      const housePayload = await enterHouse(houseId).unwrap();
      // Бэк вернул полный payload дома (wallpaper, furniture, guests и т.д.).
      // Кладём его в houseOverride, чтобы UI отрисовал дом мгновенно,
      // не дожидаясь refetch getHousesStatus.
      dispatch(setHouseOverride(housePayload));

      // Оптимистично двигаем себя в кэшах онлайна: со старой локации
      // в виртуальную комнату дома. Без этого три области (заголовок, count,
      // страница) переключатся в три разных кадра, потому что данные приходят
      // с сервера и с разными задержками.
      const globalState = chatApi.endpoints.getOnlineCharacters.select({
        locationSlug: null, limit: 50, offset: 0,
      })(storeRef.current.getState());
      const userObject = globalState?.data?.objects?.find(u => u.id === character.id);

      if (userObject) {
        moveOnlineUser(dispatch, {
          characterId: character.id,
          oldLocationSlug: character.location_slug,
          newLocationSlug: `house:${houseId}`,
          userData: userObject,
        });
      }

      dispatch(commitCharacterFields({ current_house_id: houseId }));
      dispatch(commitChatRoom(`house:${houseId}`));

      // Фоновая синхронизация с сервером (не блокирует UI).
      // forceRefetch: кэш ячейки {roomId: 'house:X'} живёт 300 сек, и при
      // повторном входе в тот же дом RTK может отдать устаревший снэпшот
      // (count: 0) без запроса к серверу.
      dispatch(chatApi.endpoints.getOnlineCharacters.initiate(
        { roomId: `house:${houseId}`, limit: 50, offset: 0 },
        { forceRefetch: true, subscribe: false }
      )).catch(() => null);

      dispatch(characterApi.util.invalidateTags(['Character']));
      refetch();
    } catch (e) {
      showError(getErrorMessage(e, 'Ошибка при входе в дом'));
    } finally {
      setBusyHouseId(null);
    }
  };

  const handleExit = async () => {
    try {
      await exitHouse().unwrap();

      const oldChatRoomId = character.chat_room_id;
      const globalState = chatApi.endpoints.getOnlineCharacters.select({
        locationSlug: null, limit: 50, offset: 0,
      })(storeRef.current.getState());
      const userObject = globalState?.data?.objects?.find(u => u.id === character.id);

      if (userObject && oldChatRoomId) {
        moveOnlineUser(dispatch, {
          characterId: character.id,
          oldLocationSlug: oldChatRoomId,
          newLocationSlug: character.location_slug,
          userData: userObject,
        });
      }

      dispatch(commitCharacterFields({ current_house_id: null }));
      dispatch(commitChatRoom(character.location_slug));
      // Сбрасываем override: без этого после выхода isInsideHouse останется
      // true (override.id всё ещё указывает на старый дом), и HousePage
      // не переключится на улицу.
      dispatch(clearHouseOverride());
      dispatch(characterApi.util.invalidateTags(['Character']));
      refetch();
    } catch (e) {
      showError(getErrorMessage(e, 'Ошибка при выходе из дома'));
    }
  };

const handleInstall = async (inventoryItemId) => {
    if (busyItemId !== null) return;
    setBusyItemId(inventoryItemId);
    try {
      const result = await installFurniture({ houseId: currentHouseId, inventoryItemId }).unwrap();
      dispatch(setHouseOverride(result.house));
      dispatch(housesApi.util.upsertQueryData('getMyFurniture', character.id, result.my_furniture));    
      dispatch(characterApi.util.invalidateTags(['Character']));
    } catch (e) {
      showError(getErrorMessage(e, 'Ошибка при установке мебели'));
    } finally {
      setBusyItemId(null);
    }
  };

  const handleUninstall = async (inventoryItemId) => {
    if (busyItemId !== null) return;
    setBusyItemId(inventoryItemId);
    try {
      const result = await uninstallFurniture({ inventoryItemId }).unwrap();
      dispatch(setHouseOverride(result.house));
      dispatch(housesApi.util.upsertQueryData('getMyFurniture', character.id, result.my_furniture));    
      dispatch(characterApi.util.invalidateTags(['Character']));
    } catch (e) {
      showError(getErrorMessage(e, 'Ошибка при снятии мебели'));
    } finally {
      setBusyItemId(null);
    }
  };

  const handleWallpaperFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedWallpaperFile(file);
      if (wallpaperPreviewUrl && wallpaperPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(wallpaperPreviewUrl);
      }
      setWallpaperPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleUploadWallpaper = async () => {
    if (!selectedWallpaperFile) {
      showError('Файл не выбран');
      return;
    }
    const allowedFormats = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedFormats.includes(selectedWallpaperFile.type)) {
      showError('Неверный формат файла. Допустимые форматы: JPEG, JPG, PNG, GIF');
      return;
    }
    try {
      const uploadedFile = await uploadFile({ file: selectedWallpaperFile }).unwrap();
      if (!isMountedRef.current) return;
      await updateHouseWallpaper({ houseId: currentHouseId, wallpaperPhotoId: uploadedFile.id }).unwrap();
      if (!isMountedRef.current) return;

      // Формируем полный payload из ближайшего источника (override → свой дом →
      // current_house с сервера). Ставим его целиком, а не патчем — тогда
      // гарантированно есть все поля, и UI читает обновлённые обои сразу.
      const baseHouse = houseOverride || currentHouse || statusData?.current_house;
      if (baseHouse) {
        dispatch(setHouseOverride({ ...baseHouse, wallpaper_photo_id: uploadedFile.id }));
      }
      setWallpaperPreviewUrl(null);
      setSelectedWallpaperFile(null);
      // refetch() НЕ вызываем: updateHouseWallpaper уже инвалидирует 'Houses',
      // RTK сам перезапросит getHousesStatus. Явный refetch создавал гонку.    

    } catch (e) {
      if (!isMountedRef.current) return;
      showError(getErrorMessage(e, 'Ошибка при загрузке обоев'));
    }
  };

  const handleDeleteWallpaper = async () => {
    try {
      await updateHouseWallpaper({ houseId: currentHouseId, wallpaperPhotoId: null }).unwrap();

      const baseHouse = houseOverride || currentHouse || statusData?.current_house;
      if (baseHouse) {
        dispatch(setHouseOverride({ ...baseHouse, wallpaper_photo_id: null }));
      }
      setWallpaperPreviewUrl(null);
      setSelectedWallpaperFile(null);    

    } catch (e) {
      showError(getErrorMessage(e, 'Ошибка при удалении обоев'));
    }
  };

  const handleKnock = async () => {
    const num = parseInt(knockHouseNumber, 10);
    if (!num || num <= 0) {
      showError('Введите корректный номер дома');
      return;
    }
    setIsKnocking(true);
    try {
      await knockHouse({ houseNumber: num }).unwrap();
      setKnockHouseNumber('');
    } catch (e) {
      showError(getErrorMessage(e, 'Не удалось постучаться'));
    } finally {
      setIsKnocking(false);
    }
  };

  const handleAcceptRequest = async (requestId) => {
    if (busyAcceptId !== null) return;
    setBusyAcceptId(requestId);
    try {
      const result = await acceptGuestRequest(requestId).unwrap();
      dispatch(setHouseOverride(result.house));
      dispatch(
        housesApi.util.updateQueryData('getHouseGuests', currentHouseId, (draft) => {
          draft.guests = result.house.guests || [];
          draft.requests = result.requests || [];
        })
      );
    } catch (e) {
      showError(getErrorMessage(e, 'Не удалось впустить гостя'));
    } finally {
      setBusyAcceptId(null);
    }
  };

  const handleRejectRequest = async (requestId) => {
    if (busyRejectId !== null) return;
    setBusyRejectId(requestId);
    try {
      const result = await rejectGuestRequest(requestId).unwrap();
      dispatch(setHouseOverride(result.house));
      dispatch(
        housesApi.util.updateQueryData('getHouseGuests', currentHouseId, (draft) => {
          draft.requests = result.requests || [];
        })
      );
    } catch (e) {
      showError(getErrorMessage(e, 'Не удалось отказать гостю'));
    } finally {
      setBusyRejectId(null);
    }
  };

  const handleKickGuest = async (characterId) => {
    if (busyGuestId !== null) return;
    setBusyGuestId(characterId);
    try {
      const result = await kickHouseGuest(characterId).unwrap();
      dispatch(setHouseOverride(result.house));
      dispatch(
        housesApi.util.updateQueryData('getHouseGuests', currentHouseId, (draft) => {
          draft.guests = result.house.guests || [];
        })
      );
    } catch (e) {
      showError(getErrorMessage(e, 'Не удалось выгнать гостя'));
    } finally {
      setBusyGuestId(null);
    }
  };

  return {
    statusData,
    houses,
    housePrice,
    maxGuests,
    isInsideHouse,
    viewedHouse,
    isOwner,
    requests,
    myFurniture,
    houseFurniture,
    isBuying,
    isExiting,
    isUpdatingWallpaper,
    isKnocking,
    activeTab,
    setActiveTab,
    busyItemId,
    busyHouseId,
    busyAcceptId,
    busyRejectId,
    busyGuestId,
    knockHouseNumber,
    setKnockHouseNumber,
    selectedWallpaperFile,
    currentError,
    handleBuy,
    handleEnter,
    handleExit,
    handleInstall,
    handleUninstall,
    handleWallpaperFileChange,
    handleUploadWallpaper,
    handleDeleteWallpaper,
    handleKnock,
    handleAcceptRequest,
    handleRejectRequest,
    handleKickGuest,
  };
};