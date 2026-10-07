import { chatApi } from '../../../entities/chat/api/chatApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { storeRef } from '../../../shared/store/storeRef';


export const ONLINE_PAGE_LIMIT = 50;
export const ONLINE_PAGE_OFFSET = 0;


// --- Примитивы (чистые функции для draft) ---

const upsertUser = (draft, userObject) => {
  // Защита: updateQueryData может передать false/undefined, если ячейка
  // не создана или запрос упал. Immer не даёт писать в примитив — выходим.
  if (!draft || typeof draft !== 'object') return false;
  if (!draft.objects) {
    draft.objects = [];
    draft.count = 0;
  }
  if (!draft.objects.some(u => u.id === userObject.id)) {
    draft.objects.unshift(userObject);
    draft.count += 1;
    return true;
  }
  return false;
};

const removeUser = (draft, characterId) => {
  if (!draft || typeof draft !== 'object') return false;
  if (!draft.objects) return false;
  const idx = draft.objects.findIndex(u => u.id === characterId);
  if (idx !== -1) {
    draft.objects.splice(idx, 1);
    draft.count = Math.max(0, draft.count - 1);
    return true;
  }
  return false;
};

export const incrementLocationCount = (draft, slug) => {
  if (!slug || !Array.isArray(draft)) return;
  const existing = draft.find(loc => loc.location_slug === slug);
  if (existing) {
    existing.count += 1;
  } else {
    draft.push({ location_slug: slug, count: 1, type: 'other' }); // Важно: type: 'other'
  }
};

export const decrementLocationCount = (draft, slug) => {
  if (!slug || !Array.isArray(draft)) return;
  const existing = draft.find(loc => loc.location_slug === slug);
  if (existing && existing.count > 0) {
    existing.count -= 1;
  }
};

// --- Композиция: перемещение пользователя между локациями ---

// Виртуальные комнаты — не локации с точки зрения карты и статистики.
// Они появляются только в чате, но не влияют на счётчики на карте мира.
const isVirtualRoom = (slug) =>
  typeof slug === 'string' && (slug.startsWith('house:') || slug === 'inn:inside');

// Обновляем ячейку только если она уже создана и содержит валидный объект.
// updateQueryData на отсутствующую ячейку создаёт её с data: undefined,
// и Immer падает при мутации. Пропускаем — данные подтянет ближайший refetch.
const safeOnlineUpdate = (dispatch, args, updater) => {
  const entry = chatApi.endpoints.getOnlineCharacters.select(args)(storeRef.current.getState());
  if (!entry || entry.status !== 'fulfilled' || !entry.data || typeof entry.data !== 'object') {
    return;
  }
  dispatch(chatApi.util.updateQueryData('getOnlineCharacters', args, updater));
};

export const moveOnlineUser = (dispatch, { 
  characterId, 
  oldLocationSlug, 
  newLocationSlug, 
  oldRealLocationSlug,
  newRealLocationSlug,
  userData 
}) => {
  if (!oldLocationSlug || oldLocationSlug === newLocationSlug || !userData) return;

  const goingVirtual = isVirtualRoom(newLocationSlug);

  // При переходе в виртуальную комнату (дом/номер) реальная локация не меняется:
  // location_slug остаётся прежним (тот, что у userData), current_room_id = new.
  // При выходе из виртуальной комнаты или обычном переходе между локациями:
  // location_slug = new, current_room_id = null.
  const userObject = {
    ...userData,
    id: characterId,
    location_slug: goingVirtual ? userData.location_slug : newLocationSlug,
    current_room_id: goingVirtual ? newLocationSlug : null,
  };

  // 1. Глобальный кэш — ключ { locationSlug: null }.
  safeOnlineUpdate(
    dispatch,
    { locationSlug: null, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
    (draft) => {
      const idx = draft.objects?.findIndex(u => u.id === characterId);
      if (idx !== undefined && idx !== -1) {
        draft.objects[idx].location_slug = userObject.location_slug;
        draft.objects[idx].current_room_id = userObject.current_room_id;
      }
    }
  );

  // 2. Старая комната — ключ { roomId: oldLocationSlug }.
  safeOnlineUpdate(
    dispatch,
    { roomId: oldLocationSlug, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
    (draft) => { removeUser(draft, characterId); }
  );

  // 3. Новая комната — ключ { roomId: newLocationSlug }.
  safeOnlineUpdate(
    dispatch,
    { roomId: newLocationSlug, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
    (draft) => { upsertUser(draft, userObject); }
  );

  // 4. Счётчики на карте. Считаются только по РЕАЛЬНЫМ локациям:
  // переход в дом/номер не меняет реальную локацию, игрок фактически
  // остаётся в 1.19.residential-area или 1.12.inn.
  // oldReal / newReal приходят из бэка в presence-событии (реальные slug-и
  // до и после перехода). Если бэк их не прислал — ничего не делаем,
  // счётчик подтянется при открытии карты.
  const oldReal = oldRealLocationSlug;
  const newReal = newRealLocationSlug;
  if (
    oldReal && newReal &&
    oldReal !== newReal &&
    !isVirtualRoom(oldReal) &&
    !isVirtualRoom(newReal)
  ) {
    dispatch(characterApi.util.updateQueryData('getLocationsStats', undefined, (draft) => {
      decrementLocationCount(draft, oldReal);
      incrementLocationCount(draft, newReal);
    }));
  }
};

// --- Композиция для usePresenceSync ---

export const setOnlineUserPresence = (dispatch, { characterId, isOnline, locationSlug, userData }) => {
  if (isOnline) {
    if (!userData) return;

    const userObject = { ...userData, location_slug: locationSlug, id: characterId };

    // Присутствие онлайн
    let wasNew = false;
    safeOnlineUpdate(
      dispatch,
      { locationSlug: null, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
      (draft) => { wasNew = upsertUser(draft, userObject); }
    );

    if (locationSlug) {
      safeOnlineUpdate(
        dispatch,
        { roomId: locationSlug, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
        (draft) => upsertUser(draft, userObject)
      );
      if (wasNew && !isVirtualRoom(locationSlug)) {
        // этот updateQueryData оставь как есть — getLocationsStats отдельный эндпоинт
        dispatch(characterApi.util.updateQueryData('getLocationsStats', undefined, (draft) => {
          incrementLocationCount(draft, locationSlug);
        }));
      }
    }
  } else {
    // Оффлайн
    let wasRemoved = false;
    safeOnlineUpdate(
      dispatch,
      { locationSlug: null, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
      (draft) => { wasRemoved = removeUser(draft, characterId); }
    );

    if (locationSlug) {
      safeOnlineUpdate(
        dispatch,
        { roomId: locationSlug, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET },
        (draft) => removeUser(draft, characterId)
      );
      if (wasRemoved && !isVirtualRoom(locationSlug)) {
        dispatch(characterApi.util.updateQueryData('getLocationsStats', undefined, (draft) => {
          decrementLocationCount(draft, locationSlug);
        }));
      }
    }
  }
};
