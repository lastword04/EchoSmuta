import { useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { getViewEntryPrefetches } from '../../../shared/config/locations/viewEntryPrefetches';
import { useLocationNavigation } from './useLocationNavigation';
import { getInitialView, normalizeViewId } from '../../../shared/config/locations/locationNavConfig';

/**
 * Обновление данных АКТИВНОЙ вкладки — каноничный механизм для кнопки
 * «Обновить» и клика по активной вкладке. Заменяет механику обновления через window-события:
 * перекачивает ровно те запросы из реестра viewEntryPrefetches, которые кормят
 * вкладку (args байт-в-байт совпадают с компонентами по построению реестра).
 */
export const useRefreshCurrentView = (locationSlug, characterId, apiSlice) => {
    const dispatch = useDispatch();
    const { navigation } = useLocationNavigation();

    return useCallback(async () => {
        if (!locationSlug || !characterId) return;

        const viewId = navigation?.activeView
            ? normalizeViewId(navigation.activeView)
            : getInitialView(locationSlug);

        const configs = getViewEntryPrefetches(locationSlug, viewId, characterId);
        
        // Вкладки вне реестра (сейчас только shop-detail: shopId живёт в стейте
        // родителя и реестру недоступен). Голый тег перечитает все СМОНТИРОВАНные
        // подписчики CityShop (ShopDetailView) и пометит stale остальные ячейки.
        if (configs.length === 0) {
            dispatch(apiSlice.util.invalidateTags(['CityShop']));
            return;
        }

        // refreshBy: 'tags' — для вкладок с пользовательскими фильтрами (поиск,
        // quantity рецептов): вместо перекачки дефолтных args помечаем несвежим
        // весь тип — RTK сам перечитает ЯЧЕЙКУ, которую реально смотрят.
        const tagTypes = new Set();
        const fetchConfigs = [];

        configs.forEach(q => {
            if (q.refreshBy === 'tags') {
                tagTypes.add(q.tagType);
            } else {
                fetchConfigs.push(q);
            }
        });

        tagTypes.forEach(tagType => {
            dispatch(apiSlice.util.invalidateTags([tagType]));
        });

        await Promise.all(
            fetchConfigs.map(q =>
                dispatch(q.api.endpoints[q.endpoint].initiate(q.args, { forceRefetch: true, subscribe: false }))
                    .catch(() => null)
            )
        );
    }, [locationSlug, characterId, navigation?.activeView, dispatch, apiSlice]);
};