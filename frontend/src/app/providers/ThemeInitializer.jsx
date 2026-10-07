import { useEffect } from 'react';
import { useSelector } from 'react-redux';

export const ThemeInitializer = () => {
  // Читаем тему из Redux (из ветки local, как у тебя настроено)
  const mode = useSelector((state) => state.local?.mode ?? 'day');
  const isNight = mode === 'night';
  
  useEffect(() => {
    // Применяем классы к <html> и <body>
    document.documentElement.classList.toggle('night-mode', isNight);
    document.body.classList.toggle('night-mode', isNight);
    
    // Добавляем data-атрибут для CSS-переменных (опционально, но удобно)
    document.documentElement.setAttribute('data-theme', mode);
    
    // Функция очистки при размонтировании (на всякий случай)
    return () => {
      document.documentElement.classList.remove('night-mode');
      document.body.classList.remove('night-mode');
      document.documentElement.removeAttribute('data-theme');
    };
  }, [isNight, mode]); // Перезапускаем эффект при смене темы
  
  // Компонент ничего не рендерит в DOM
  return null;
};