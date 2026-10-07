// === ЛИМИТЫ ПЕРСОНАЖА ===
export const MINING_LIMITS = {
  MIN_LEVEL: 3,
  MAX_TIREDNESS: 0.495,
};

// === СТАТУСЫ МАЙНИНГА ===
export const MINING_STATUS = {
  IDLE: 'idle',
  IN_PROGRESS: 'in_progress',
  DONE: 'done',
};

// === КОДЫ ОШИБОК API ===
export const MINING_ERRORS = {
  CAPTCHA_EXPIRED: 'CAPTCHA_EXPIRED',
  INVALID_CAPTCHA_INPUT: 'INVALID_CAPTCHA_INPUT',
  INSUFFICIENT_CHARACTER_LEVEL: 'INSUFFICIENT_CHARACTER_LEVEL',
  INSUFFICIENT_CHARACTER_TIREDNESS: 'INSUFFICIENT_CHARACTER_TIREDNESS',
};

// === ТАЙМИНГИ (в миллисекундах) ===
export const MINING_TIMERS = {
  POLLING_INTERVAL: 1000,       // ✅ Было 200, стало 1000 (1 секунда)
  FOCUS_DELAY: 50,
  CAPTCHA_PREFETCH_AT: 5,
  TIMER_TICK: 500,
};

// === РЕГУЛЯРКИ ===
export const MINING_REGEX = {
  CAPTCHA_INPUT: /^\d{0,3}$/,           // Ввод капчи: только цифры, до 3 знаков  
  MINING_MESSAGE: /^(.+?)\s+(\d+)$/,    // ✅ для разделения текста и времени
};

// === UI ===
export const MINING_UI = {
  TIMER_COLOR: '#d7980d',
  ERROR_COLOR: 'red',
  MARGIN_TOP: '.5rem',
};

// === ПУТИ К РЕСУРСАМ ===
export const MINING_PATHS = {
  LOCATION_BG: (slug) => `/images/locations/backgrounds/${slug}.png`,
  RESOURCE_ICON: (slug) => `/images/resources/${slug}.png`,
};

// === ШИРИНЫ КОЛОНОК ПО ЛОКАЦИЯМ ===
export const LOCATION_COLUMN_WIDTHS = {
  '2.4.lake': ['20.54%', '30.66%', '25.11%', '12.69%', '11%'],
  // Добавляй другие локации по мере необходимости
};

/**
 * Парсит сообщение майнинга вида "Добыча завершится через 120"
 * @param {string} rawMessage - сырое сообщение от API
 * @returns {{ text: string, seconds: number }}
 */
/**
 * Парсит сообщение майнинга/крафта.
 * Поддерживает два формата:
 * - "Вы варите ... Осталось 60 сек." → убирает "Осталось 60 сек.", возвращает секунды
 * - "Вы рубите деревья еще 32" → убирает число в конце, возвращает секунды
 * @param {string} rawMessage - сырое сообщение от API
 * @returns {{ text: string, seconds: number }}
 */
export const parseMiningMessage = (rawMessage) => {
  if (!rawMessage || typeof rawMessage !== 'string') {
    return { text: '', seconds: 0 };
  }

  const trimmed = rawMessage.trim();
  let seconds = 0;
  let text = trimmed;

  // 1. Ищем "Осталось X сек." (с точкой или без)
  const timeMatch = trimmed.match(/Осталось\s+(\d+)\s*сек\.?/i);
  if (timeMatch) {
    seconds = parseInt(timeMatch[1], 10);
    text = trimmed.replace(/Осталось\s+\d+\s*сек\.?/i, '').trim();
  } else {
    // 2. Запасной вариант: число в конце (без "Осталось")
    const fallbackMatch = trimmed.match(/(\d+)$/);
    if (fallbackMatch) {
      seconds = parseInt(fallbackMatch[1], 10);
      text = trimmed.replace(/\s*\d+$/, '').trim();
    }
  }

  return { text, seconds };
};