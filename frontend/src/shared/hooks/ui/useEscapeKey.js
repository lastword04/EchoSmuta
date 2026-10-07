import { useEffect } from 'react';

/**
 * Вызывает callback при нажатии Escape.
 * @param {Function} callback - функция, которую нужно вызвать
 * @param {boolean} isActive - слушать ли события (по умолчанию true)
 */
export const useEscapeKey = (callback, isActive = true) => {
  useEffect(() => {
    if (!isActive) return;
    
    const handleEsc = (e) => {
      if (e.key === 'Escape') callback();
    };
    
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [callback, isActive]);
};