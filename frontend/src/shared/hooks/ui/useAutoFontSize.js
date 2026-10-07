import { useEffect, useRef, useCallback } from 'react';

/**
 * Автоматически подстраивает размер шрифта, чтобы текст вмещался по ширине.
 * @param {number} maxWidth - Максимальная ширина текста (0 = брать ширину родителя)
 * @param {number} initialSize - Начальный размер шрифта
 * @param {number} minSize - Минимально допустимый размер шрифта
 * @param {number} padding - Отступы, которые вычитаются из доступной ширины
 */
export const useAutoFontSize = (maxWidth = 0, initialSize = 16, minSize = 10, padding = 0) => {
  const ref = useRef(null);
  const lastFontSize = useRef(initialSize);

  const adjustFontSize = useCallback(() => {
    const el = ref.current;
    if (!el) return;

    const parentWidth = el.parentElement?.getBoundingClientRect()?.width || 200;
    const targetWidth = maxWidth > 0 ? maxWidth : (parentWidth - padding);

    // используем последний известный размер (не сбрасываем при каждом рендере)
    let currentSize = lastFontSize.current || initialSize;

    // если элемент случайно вырос (например, после пересоздания) — ограничим
    if (currentSize > initialSize) currentSize = initialSize;

    el.style.whiteSpace = 'nowrap';
    el.style.fontSize = `${currentSize}px`;

    // уменьшаем шрифт, пока текст не влезет в контейнер
    while (el.scrollWidth > targetWidth && currentSize > minSize) {
      currentSize -= 1;
      el.style.fontSize = `${currentSize}px`;
    }

    lastFontSize.current = currentSize;
  }, [maxWidth, initialSize, minSize, padding]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
  
    // двойной requestAnimationFrame гарантирует корректный расчёт после рендера
    /*requestAnimationFrame(() => adjustFontSize());
    requestAnimationFrame(() => adjustFontSize());*/

   const resizeObserver = new ResizeObserver(() => {
      adjustFontSize();
    });
    resizeObserver.observe(el.parentElement);
    /*resizeObserver.observe(el);*/

    // реагируем на изменения текста
    const mutationObserver = new MutationObserver(() => adjustFontSize());
    mutationObserver.observe(el, { childList: true, characterData: true, subtree: true });

    // реагируем на изменение окна
    const handleResize = () => adjustFontSize();
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    return () => {
      resizeObserver.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, [adjustFontSize]);

  return ref;
};
