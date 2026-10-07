import { useCallback, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { moveOnlineUser, decrementLocationCount, incrementLocationCount, ONLINE_PAGE_LIMIT, ONLINE_PAGE_OFFSET } from '../lib/onlineCacheSync';
import { storeRef } from '../../../shared/store/storeRef';
import { characterApi } from '../../../entities/character/api/characterApi';
import { chatApi, chatHistoryArgs } from '../../../entities/chat/api/chatApi';
import { getLocationEntryPrefetches } from '../../../shared/config/locations/locationEntryPrefetches';
import { getViewEntryPrefetches } from '../../../shared/config/locations/viewEntryPrefetches';
import { useLocationNavigation } from '../../../shared/hooks/location/useLocationNavigation';
import { getInitialView } from '../../../shared/config/locations/locationNavConfig';
import { clearLastMining } from '../../../entities/resources/store/miningSlice';
import { commitLocation, setLocation } from '../../../entities/character/store/characterSlice';

/**
 * Владеет логикой перехода между локациями:
 * бэкенд (changeLocation) + префетчи (RTK Query) + Redux (navigation) + character state.
 * 
 * withBasePage получает только handleLocationChange.
 *
 * Оптимистично обновляет кэши онлайна в один тик с commitLocation
 * для атомарного UI-обновления. Presence-событие придёт позже, но usePresenceSync
 * идемпотентен (проверка exists) — дубликат проигнорирует.
 *
 * Модалка карты закрывается в том же коммите, что и переключение страницы
 * (confirm + select + commitLocation + setActiveModal), чтобы между кликом.        
 * и новой локацией не показывался промежуточный кадр старой страницы.
 */

export const useLocationTransition = (character, setActiveModal, showError) => {
    const dispatch = useDispatch();
    const [changeLocation] = characterApi.endpoints.changeLocation.useMutation();
    const activeCharacterId = useSelector(state => state.local.activeCharacterId);
    const { select, requestLocationChange, confirm, fail } = useLocationNavigation();
    
    const isTransitioningRef = useRef(false);

    // Актуальный character без stale-замыкания внутри useCallback
    const characterRef = useRef(character);
    useEffect(() => {
        characterRef.current = character;
    }, [character]);

    const handleLocationChange = useCallback(async (targetLocationSlug, options = {}) => {
        if (isTransitioningRef.current) return;
        
        
        isTransitioningRef.current = true;
        const requestId = requestLocationChange(targetLocationSlug);
        let locationChanged = false;
        let updatedCharacter = null;
        
        try {
            // 1. Получаем единый список префетчей для НОВОЙ локации.
            // Они уже содержат правильные аргументы (включая parentSlug, если он отличается).
            const prefetchConfigs = getLocationEntryPrefetches(targetLocationSlug, activeCharacterId);                    
            
            const oldLocationSlug = characterRef.current?.location_slug;

           // Критический путь: только ОБЯЗАТЕЛЬНЫЕ префетчи дефолтной вкладки.
            // .catch: 404 («нет лавки/лицензии») — валидный ответ, а не сбой перехода
            const FRESH_MS = 60 * 1000; // повторный переход в течение минуты — из кэша

            const initiatePrefetch = (q) => {
                const entry = q.api.endpoints[q.endpoint].select(q.args)(storeRef.current.getState());
                    const isFresh = entry?.status === 'fulfilled' &&
                    !entry.isInvalidated &&
                    entry?.fulfilledTimeStamp &&
                    (Date.now() - entry.fulfilledTimeStamp) < FRESH_MS;

                return dispatch(q.api.endpoints[q.endpoint].initiate(q.args, {
                    forceRefetch: !isFresh || q.alwaysFresh === true,
                    subscribe: false,
                })).catch(() => null);
            };

            const seenPrefetchKeys = new Set();

            // Целевая вкладка физического перехода (options.targetView):
            // её данные тоже должны быть в кэше к монтированию, иначе view
            // рисует null-кадры (мелькание при входе в «Вашу аптеку» и т.п.)
            const targetViewConfigs = options.targetView
                ? getViewEntryPrefetches(targetLocationSlug, options.targetView, activeCharacterId)
                : [];

            // 1. СНАЧАЛА переезд: сервер должен записать новую локацию персонажа.
            updatedCharacter = await changeLocation(targetLocationSlug).unwrap();
            locationChanged = true;

            // После смены локации бэк мог выполнить автовход в номер гостиницы
            // (если у игрока активная аренда). В этом случае актуальная чат-комната
            // уже не targetLocationSlug, а 'inn:inside'. Все чат-префетчи ниже
            // должны идти по ней, а не по локации — иначе чат сядет на «холодный» кэш.
            const newChatRoomId = updatedCharacter.current_room_id ?? targetLocationSlug;
            const oldChatRoomId = characterRef.current?.chat_room_id ?? oldLocationSlug;

            // 2. ТОЛЬКО ТЕПЕРЬ запускаем префетчи (именно здесь, после переезда):
            // сервер уже видит персонажа на новом месте и вернёт реальные данные.
            const requiredPrefetchPromises = [
                ...prefetchConfigs.filter(q => q.required),
                ...targetViewConfigs,
            ]
                // Дедупликация: целевая вкладка может пересекаться с дефолтной
                .filter(q => {
                    const key = `${q.api.reducerPath}:${q.endpoint}:${JSON.stringify(q.args)}`;
                    if (seenPrefetchKeys.has(key)) return false;
                    seenPrefetchKeys.add(key);
                    return true;
                })
                .map(initiatePrefetch);          

            // Смена локации + обязательные данные — параллельно.
            // unwrap(): ошибка сервера теперь реально попадает в catch
            const onlinePrefetchPromise = dispatch(chatApi.endpoints.getOnlineCharacters.initiate({ roomId: newChatRoomId, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET }, { forceRefetch: true, subscribe: false })).catch(() => null);
                 
            await Promise.all([
                ...requiredPrefetchPromises,
                onlinePrefetchPromise,
            ]);

            // 8. Оптимистично синхронизируем кэши онлайна с предстоящей сменой character.
            // dispatch'и ниже и commitLocation попадают в один тик React 18 → UI видит атомарно.          
            if (oldChatRoomId && oldChatRoomId !== newChatRoomId) {
                const globalState = chatApi.endpoints.getOnlineCharacters.select({ 
                    locationSlug: null, 
                    limit: ONLINE_PAGE_LIMIT, 
                    offset: ONLINE_PAGE_OFFSET
                })(storeRef.current.getState());
                const userObject = globalState?.data?.objects?.find(u => u.id === activeCharacterId);

                if (userObject) {
                    moveOnlineUser(dispatch, {
                        characterId: activeCharacterId,
                        oldLocationSlug: oldChatRoomId,
                        newLocationSlug: newChatRoomId,
                        oldRealLocationSlug: oldLocationSlug,
                        newRealLocationSlug: targetLocationSlug,
                        userData: userObject,
                    });
                }
            }            
            

            // 9. Успешно завершаем переход
            confirm(requestId);
            select(options.targetView || getInitialView(targetLocationSlug));
            // Кэш getOnlyMe больше не инвалидируется мутацией — пишем ответ в него
            // тем же тиком: снапшот-читатели (мастерская) видят новую локацию сразу
            dispatch(
                characterApi.util.updateQueryData('getOnlyMe', undefined, (draft) => {
                    Object.assign(draft, updatedCharacter);
                })
            );
            dispatch(commitLocation({ locationSlug: targetLocationSlug, character: updatedCharacter }));
            setActiveModal(null);
                             
            dispatch(clearLastMining());

            // ── Фон: необязательные данные + чат. Едут ПОСЛЕ атомарного переключения ──
            prefetchConfigs
                .filter(q => !q.required)
                .forEach(initiatePrefetch)

            const activeTab = storeRef.current.getState().session.activeTab;
            const activeRoom = activeTab === 'Локация' ? newChatRoomId : 'global';
            [
                chatApi.endpoints.getMySettings.initiate(undefined, { forceRefetch: true, subscribe: false }),
                chatApi.endpoints.getChatHistory.initiate(chatHistoryArgs(activeRoom, null), { forceRefetch: true, subscribe: false }),
                chatApi.endpoints.getChatHistory.initiate(chatHistoryArgs(activeRoom, newChatRoomId), { forceRefetch: true, subscribe: false }),

            ].forEach(p => { dispatch(p).catch(() => null); });
            
        } catch (error) {
            console.error('Error changing location:', error);
            setActiveModal(null);
            if (locationChanged) {
                if (updatedCharacter) {
                    dispatch(
                        characterApi.util.updateQueryData('getOnlyMe', undefined, (draft) => {
                            Object.assign(draft, updatedCharacter);
                        })
                    );
                }
                dispatch(
                    updatedCharacter
                        ? commitLocation({ locationSlug: targetLocationSlug, character: updatedCharacter })
                        : setLocation(targetLocationSlug)
                );
                confirm(requestId);
                select(options.targetView || getInitialView(targetLocationSlug));
                showError('Локация изменена, но данные загрузились не полностью');
            } else {
                fail(requestId);
                showError('Ошибка смены локации');
            }
        } finally {
            isTransitioningRef.current = false;
        }
    }, [activeCharacterId, changeLocation, dispatch, requestLocationChange, confirm, select, fail, setActiveModal, showError]);

    return { handleLocationChange };
};