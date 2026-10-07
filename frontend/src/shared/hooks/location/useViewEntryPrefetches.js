import { useCallback, useRef } from 'react';
import { useDispatch } from 'react-redux';

import { storeRef } from '../../store/storeRef';
import { getViewEntryPrefetches } from '../../../shared/config/locations/viewEntryPrefetches';
import { useLocationNavigation } from './useLocationNavigation';

const GATE_TIMEOUT_MS = 3000; // предохранитель: зависший запрос не блокирует навигацию навсегда

/**
 * Атомарный переход между вкладками: если данных вкладки нет в кэше
 * (или они инвалидированы событием) — дождаться загрузки и только потом
 * переключить вкладку. Старая вкладка остаётся на экране полной и живой.
 *
 * Правила:
 *  - данные в кэше и свежие → мгновенное переключение;
 *  - данные инвалидированы (событие экономики) → дождаться рефетча,
 *    показать сразу свежие — без «сначала старое, потом новое»;
 *  - вкладка без записей в реестре → мгновенно.
 */
export const useViewEntryPrefetches = (locationSlug, characterId) => {
    const dispatch = useDispatch();
    const { select } = useLocationNavigation();
    const isNavigatingRef = useRef(false);

    const requestView = useCallback(async (viewId) => {
        if (isNavigatingRef.current) return;
        const configs = getViewEntryPrefetches(locationSlug, viewId, characterId);

        // Проверяем кэш: грузить нужно, если данных нет или они помечены событием
        const needsFetch = configs.some(q => {
            const entry = q.api.endpoints[q.endpoint].select(q.args)(storeRef.current.getState());
            return entry?.data === undefined || entry.isInvalidated;
        });

        if (!needsFetch) {
            select(viewId);
            return;
        }

        isNavigatingRef.current = true;
        try {
            // initiate без forceRefetch: отсутствие данных → загрузка,
            // инвалидированный кэш → рефетч, свежий кэш → мгновенный резолв
            await Promise.race([
                Promise.all(configs.map(q =>                    
                    dispatch(q.api.endpoints[q.endpoint].initiate(q.args, { subscribe: false })).catch(() => null)
                )),
                new Promise(res => setTimeout(res, GATE_TIMEOUT_MS)),
            ]);
        } finally {
            // Даже при таймауте переключаем — аварийная деградация лучше мёртвой кнопки
            select(viewId);
            isNavigatingRef.current = false;
        }
    }, [locationSlug, characterId, dispatch, select]);

    return { requestView };
};