// Глобальное управление видимостью скроллбаров.
// Перенесено из app/index.jsx (этап B рефакторинга структуры, 09.2026) без
// изменения логики: скроллбар виден во время скролла и скрывается через 1с
// простоя; обрабатываются и уже существующие, и все новые элементы
// (MutationObserver). Вызывается один раз из app/index.jsx.

export const setupGlobalScrollHiding = () => {
  const scrollableElements = new Map();

  const setupScrollHiding = (el) => {
    const computedStyle = window.getComputedStyle(el);
    const overflowY = computedStyle.overflowY;

    if (overflowY === 'visible' || overflowY === 'hidden') {
      return;
    }

    const hasVerticalScroll = el.scrollHeight > el.clientHeight;
    const isTextarea = el.tagName === 'TEXTAREA';

    if (!isTextarea && !hasVerticalScroll) {
      return;
    }

    if (scrollableElements.has(el)) {
      return;
    }

    el.style.setProperty('--show-scroll', '1');

    const data = {
      hasScrolled: false,
      lastScrollTop: el.scrollTop,
      hideTimeout: null,
      isScrolling: false,
      programmaticScroll: false,
    };

    el._scrollData = data;

    const handleScroll = () => {
      const currentScrollTop = el.scrollTop;

      if (currentScrollTop !== data.lastScrollTop) {
        if (data.programmaticScroll) {
          data.programmaticScroll = false;
          data.lastScrollTop = currentScrollTop;
          return;
        }

        if (!data.isScrolling) {
          el.style.setProperty('--show-scroll', '1');
          data.isScrolling = true;
        }

        data.hasScrolled = true;
        data.lastScrollTop = currentScrollTop;
      }

      if (data.hideTimeout) clearTimeout(data.hideTimeout);

      if (data.hasScrolled) {
        data.hideTimeout = setTimeout(() => {
          el.style.setProperty('--show-scroll', '0');
          data.isScrolling = false;
        }, 1000);
      }
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    data.handler = handleScroll;

    if (isTextarea) {
      const handleInput = () => {
        const nowScrollable = el.scrollHeight > el.clientHeight;
        const alreadyTracked = scrollableElements.has(el);

        if (nowScrollable && !alreadyTracked) {
          setupScrollHiding(el);
          return;
        }

        if (nowScrollable) {
          el.style.setProperty('--show-scroll', '1');
          clearTimeout(data.hideTimeout);
          data.hideTimeout = setTimeout(() => {
            el.style.setProperty('--show-scroll', '0');
            data.isScrolling = false;
          }, 1000);
        }
      };

      el.addEventListener('input', handleInput);
      data.inputHandler = handleInput;
    }

    scrollableElements.set(el, data);
  };

  const processExistingElements = () => {
    const allEls = document.querySelectorAll('*');
    allEls.forEach(setupScrollHiding);
  };

  setTimeout(processExistingElements, 100);
  setTimeout(processExistingElements, 500);
  setTimeout(processExistingElements, 1000);

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          setupScrollHiding(node);
          node.querySelectorAll?.('*').forEach(setupScrollHiding);
        }
      });
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  return () => {
    observer.disconnect();
    scrollableElements.forEach((data, el) => {
      if (data.hideTimeout) {
        clearTimeout(data.hideTimeout);
      }
      el.removeEventListener('scroll', data.handler);
      if (data.inputHandler) el.removeEventListener('input', data.inputHandler);
      el.style.removeProperty('--show-scroll');
      delete el._scrollData;
    });
  };
};
