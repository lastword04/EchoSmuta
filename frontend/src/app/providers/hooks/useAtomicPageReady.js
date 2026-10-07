import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { storeRef } from '../../../shared/store/storeRef';
import { ONLINE_PAGE_LIMIT, ONLINE_PAGE_OFFSET } from '../lib/onlineCacheSync';

import { getLocationEntryPrefetches } from '../../../shared/config/locations/locationEntryPrefetches';
import { chatApi, chatHistoryArgs } from '../../../entities/chat/api/chatApi';

/**
 * Атомарный Boot Gate: скрывает overlay только когда данные дефолтной
 * вкладки И чат загружены (или при ошибке/таймауте — аварийная деградация).
 *
 * Сбрасывается при смене activeCharacterId (логин/F5). При этом инвалидирует
 * чат-кэши: RTK-кэш переживает SPA-логаут, и события произошедшие пока
 * персонаж был офлайн не могли его обновить — снапшоты несвежие.
 *
 * Чат гейтится ЗДЕСЬ, а не в конфиге локаций: чат есть на каждой странице,
 * независимо от дефолтной вкладки локации.
 *
 * Готовность проверяется по фактическому состоянию RTK-кэша (через storeRef),
 * а не по резолву промисов initiate — промисы могут резолвиться дедупом/из кэша.
 */
const TIMEOUT_MS = 4000;      // предохранитель: никакого бесконечного белого экрана
const MAX_ATTEMPTS = 6;       // кап на попытки: защита от retry-storm при быстрых ошибках
const RETRY_DELAY_MS = 250;   // пауза между попытками (не дольше остатка до дедлайна)

const invalidateChatCaches = (dispatch) => {
    dispatch(chatApi.util.invalidateTags([
        { type: 'OnlineUsers' },
        { type: 'ChatSettings' },
        { type: 'ChatHistory' },
    ]));
};

export const useAtomicPageReady = (character, locationSlug) => {
    const [showContent, setShowContent] = useState(false);
    const dispatch = useDispatch();
    const activeCharacterId = useSelector(state => state.local.activeCharacterId);
    const activeTab = useSelector(state => state.session.activeTab);

    // Сброс при смене персонажа (логин/F5).
    // ⚠️ Этот эффект обязан выполняться РАНЬШЕ гейт-эффекта ниже (React запускает
    // эффекты в порядке объявления — не менять порядок!). Инвалидация должна
    // случиться до того, как гейт прочитает status из кэша, иначе гейт увидит
    // устаревшие fulfilled-записи прошлого персонажа и откроется со снапшотами.
    useEffect(() => {
        setShowContent(false);
        invalidateChatCaches(dispatch);
    }, [activeCharacterId, dispatch]);

    useEffect(() => {
        if (!character?.id || !activeCharacterId) return;

        let stopped = false;

        // Для чата используем chat_room_id, если он есть (внутри дома/номера),
        // иначе обычный location_slug. UI-префетчи локации ниже работают
        // по location_slug, как и раньше.
        const chatRoomId = character.chat_room_id ?? locationSlug;
        const activeRoom = activeTab === 'Локация' ? chatRoomId : 'global';

        // Запросы дефолтной вкладки локации (из конфига) + чат: настройки,
        // онлайн обеих вкладок и история активной комнаты. Историю берём
        // в двух вариантах: флаг filter_location_messages станет известен
        // только из настроек, а компонент подпишется на свой ключ.
        const requiredQueries = [
            ...getLocationEntryPrefetches(locationSlug, activeCharacterId)
                .filter(q => q.required),
            { api: chatApi, endpoint: 'getMySettings', args: undefined },
            { api: chatApi, endpoint: 'getOnlineCharacters', args: { locationSlug: null, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET } },
            { api: chatApi, endpoint: 'getOnlineCharacters', args: { roomId: chatRoomId, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET } },
            { api: chatApi, endpoint: 'getChatHistory', args: chatHistoryArgs(activeRoom, null) },
            { api: chatApi, endpoint: 'getChatHistory', args: chatHistoryArgs(activeRoom, chatRoomId) },
        ];

        const readStore = () => {
            const state = storeRef.current?.getState();
            if (!state) {
                console.error('useAtomicPageReady: storeRef не заполнен — гейт не может проверить кэш, будет деградация по таймауту');
            }
            return state;
        };

        const isFulfilled = (q, state) =>
            q.api.endpoints[q.endpoint].select(q.args)(state)?.status === 'fulfilled';

        const getMissing = () => {
            const state = readStore();
            // Не знаем статус → считаем всё незагруженным (timeout всё равно деградирует)
            if (!state) return requiredQueries;
            return requiredQueries.filter(q => !isFulfilled(q, state));
        };

        // Предохранитель: аварийная деградация. Останавливает цикл через stopped.
        const timeout = setTimeout(() => {
            stopped = true;
            setShowContent(true);
        }, TIMEOUT_MS);

        (async () => {
            const deadline = Date.now() + TIMEOUT_MS;
            let attempt = 0;
            let missing = getMissing();

            // Кап + дедлайн: максимум MAX_ATTEMPTS попыток, но не дольше TIMEOUT_MS.
            // Кап защищает от retry-storm при быстрых ошибках сервера,
            // дедлайн — от зависания на медленных ответах.
            while (missing.length > 0 && attempt < MAX_ATTEMPTS && Date.now() < deadline) {
                attempt++;

                // ⚠️ subscribe: false — обязательно. initiate без него оставляет ВЕЧНУЮ
                // подписку (отписки нет ни в cleanup, ни где-либо ещё): RTK считает ячейку
                // «живой» навсегда. Последствия были:
                //   1) инвалидация тега (например, WorkshopRecipes от buyRecipe) вместо
                //      removeQueryResult делала немедленный refetch этой фантомной ячейки —
                //      лишний GET сразу после покупки, причём с args НА МОМЕНТ ЛОГИНА
                //      (другая локация → сервер фильтрует по зданию и отвечает []);
                //   2) ячейка оставалась status:fulfilled и НЕ invalidated → useViewEntryPrefetches
                //      и useXxxQuery считали кэш свежим и НЕ запрашивали сток при входе
                //      в мастерскую («Нет рецептов в стоке» до ручного «Обновить»).
                //
                // ⚠️ БЕЗ forceRefetch: fulfilled отфильтрованы выше, rejected повторятся
                // и так (у rejected-записи нет data), а in-flight запросы дедуплицируются.
                // forceRefetch ломал дедуп → дубли запросов в dev/StrictMode и гонки
                // с чужими подписками (двойная запись в кэш, риск для ChatHistory-merge).
                await Promise.all(
                    missing.map(q =>
                        dispatch(q.api.endpoints[q.endpoint].initiate(q.args, { subscribe: false }))
                            .catch(() => null)
                    )
                );
                if (stopped) return;

                // Перепроверяем кэш сразу: на happy path выходим без RETRY_DELAY_MS.
                // Спим только если что-то реально не загрузилось.
                missing = getMissing();
                if (missing.length === 0) break;

                const left = deadline - Date.now();
                if (left <= 0) break;
                // Экспоненциальный backoff с потолком 1с: 6 попыток растягиваются
                // на ~3.75с (250+500+1000+1000+1000), то есть окно восстановления
                // ≈ весь бюджет TIMEOUT_MS, а число запросов всё равно ≤ 6 раундов.
                const backoff = Math.min(RETRY_DELAY_MS * 2 ** (attempt - 1), 1000);
                await new Promise(r => setTimeout(r, Math.min(backoff, left)));
                if (stopped) return;
            }

            clearTimeout(timeout);
            if (!stopped) setShowContent(true);
        })();

        return () => {
            stopped = true;
            clearTimeout(timeout);
        };
    }, [character?.id, activeCharacterId, locationSlug, character?.chat_room_id, activeTab, dispatch]);

    return { showContent };
};