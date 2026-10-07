import { useSelector } from 'react-redux';

export const useTheme = () => {
  // Читаем mode из Redux (из ветки local, как у тебя настроено)
  // Если mode ещё не загрузился — используем 'day' по умолчанию
  const mode = useSelector((state) => state.local?.mode ?? 'day');
  
  // Удобные производные значения
  const isNight = mode === 'night';
  const themeClass = isNight ? 'night' : 'day';
  
  // Возвращаем объект с полезными данными
  return {
    mode,        // 'day' | 'night' — сырое значение
    isNight,     // true | false — удобно для условий
    themeClass,  // 'day' | 'night' — удобно для CSS-классов
  };
};