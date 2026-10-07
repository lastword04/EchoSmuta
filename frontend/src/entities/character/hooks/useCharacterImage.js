// src/entities/character/hooks/useCharacterImage.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { config } from '../../../shared/config/env/env';

const FILES_BASE = config.FILE_API_BASE_URL;

/**
 * URL картинки персонажа через бэкенд-редирект (302 на свежую presigned-ссылку).
 * При ошибке загрузки: первая — тихий ретрай (?retry ломает HTTP-кеш),
 * вторая — error=true (компонент показывает заглушку).
 * @param {string|null} photoId - ID фотографии
 * @param {'content'|'portrait'} mode - эндпоинт: 'content' (с авторизацией) или 'portrait' (публичный)
 */
export const useCharacterImage = (photoId, mode = 'content') => {
  const [image, setImage] = useState(null);
  const [error, setError] = useState(false);
  const retriedRef = useRef(false); // был ли уже ретрай для текущей картинки

  useEffect(() => {
    retriedRef.current = false; // новая картинка — новый шанс на ретрай
    setError(false);
    setImage(photoId ? `${FILES_BASE}/${photoId}/${mode}` : null);
  }, [photoId, mode]);

  // Единый обработчик ошибки <img>: раз решаем здесь, компоненты ничего не знают
  const handleImageError = useCallback(() => {
    if (!photoId) return;

    if (!retriedRef.current) {
      // первая ошибка — перезапрашиваем с уникальным URL
      retriedRef.current = true;
      setImage(`${FILES_BASE}/${photoId}/${mode}?retry=${Date.now()}`);
    } else {
      // вторая — сдаёмся, пусть компонент показывает заглушку
      setError(true);
      setImage(null);
    }
  }, [photoId, mode]);

  // Принудительная перезагрузка с нуля (на будущее/для кнопки «обновить»)
  const reload = useCallback(() => {
    if (!photoId) return;
    retriedRef.current = false;
    setError(false);
    setImage(`${FILES_BASE}/${photoId}/${mode}?retry=${Date.now()}`);
  }, [photoId, mode]);

  return {
    image,
    loading: false, // картинкой управляет браузер, скелетоны не нужны
    error,
    setError,
    handleImageError,
    reload
  };
};