import { useState, useCallback } from 'react';
import { resourcesApi } from '../api/resourcesApi';
import { storeRef } from '../../../shared/store/storeRef';
import { adaptResourceForCard } from '../ui/ResourceInfoCard/adaptResourceForCard';

/**
 * Хук для открытия карточки ресурса с приоритетом на кэш
 * @param {Array} cachedResources - массив уже загруженных ресурсов (myResources)
 * @returns {Function} openResource(slug) - асинхронная функция открытия
 * @returns {Object|null} selectedResource - выбранный ресурс для карточки
 * @returns {Function} closeResource - закрыть карточку
 */
export const useResourceInfo = (cachedResources = []) => {
  const [selectedResource, setSelectedResource] = useState(null);

  const openResource = useCallback(async (slug) => {
    // Быстрый путь: ищем в кэше
    const cached = cachedResources.find(r =>
      (r.resource_slug || r.slug) === slug
    );
    // Кэш пригоден, только если в нём есть цена и вес: объекты из GET /resources/my
    // (myResources) этих полей не содержат — иначе карточка показала бы нули.
    if (cached && cached.price != null && cached.weight != null) {
      setSelectedResource(adaptResourceForCard(cached));
      return;
    }
    // Фолбэк: загружаем с сервера (GET /resources/{slug} возвращает price и weight)
    try {
      const data = await storeRef.current
        .dispatch(resourcesApi.endpoints.getResourceBySlug.initiate(slug, { forceRefetch: true }))
        .unwrap();
      setSelectedResource(adaptResourceForCard(data));
    } catch (e) {
      // Сервер недоступен — показываем хотя бы кэш (имя), иначе ничего
      if (cached) setSelectedResource(adaptResourceForCard(cached));
      else console.error('Ошибка загрузки ресурса:', e);
    }
  }, [cachedResources]);

  const closeResource = useCallback(() => {
    setSelectedResource(null);
  }, []);

  return { selectedResource, openResource, closeResource };
};