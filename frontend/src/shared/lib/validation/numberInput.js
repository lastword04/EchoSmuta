const cache = {};

const intRegex = (maxDigits) => {
  if (!cache[`i${maxDigits}`]) {
    cache[`i${maxDigits}`] = new RegExp(`^\\d{1,${maxDigits}}$`);
  }
  return cache[`i${maxDigits}`];
};

const decimalRegex = (maxInt, maxFrac) => {
  const key = `d${maxInt}-${maxFrac}`;
  if (!cache[key]) {
    cache[key] = new RegExp(`^\\d{0,${maxInt}}(\\.\\d{0,${maxFrac}})?$`);
  }
  return cache[key];
};

/**
 * Целое число (кол-во): максимум maxDigits цифр.
 * onChange={intInputHandler(setter)}
 *
 * options.strip = true — «мягкий» режим: вырезает всё кроме цифр
 * и обрезает до maxDigits, вместо отклонения ввода целиком.
 * Удобно для полей, куда часто вставляют из буфера (Ctrl+V).
 */
export const intInputHandler = (setter, maxDigits = 7, options = {}) => (e) => {
  const { strip = false } = options;

  if (strip) {
    const cleaned = e.target.value.replace(/\D/g, "").slice(0, maxDigits);
    setter(cleaned);
    return;
  }

  const val = e.target.value;
  if (val === "" || intRegex(maxDigits).test(val)) setter(val);
};

/**
 * Дробное число (цена): запятая → точка,
 * до maxInt цифр до точки, до maxFrac после.
 * onChange={decimalInputHandler(setter)}
 */
export const decimalInputHandler = (setter, maxInt = 7, maxFrac = 2, options = {}) => (e) => {
  const { strip = false } = options;

  if (strip) {
    // оставляем только цифры и первую точку/запятую
    let cleaned = e.target.value.replace(',', '.');
    cleaned = cleaned.replace(/[^\d.]/g, '');
    const firstDot = cleaned.indexOf('.');
    if (firstDot !== -1) {
      cleaned = cleaned.slice(0, firstDot + 1) + cleaned.slice(firstDot + 1).replace(/\./g, '');
    }
    // обрезаем по maxInt / maxFrac
    const [intPart = '', fracPart = ''] = cleaned.split('.');
    const intTrimmed = intPart.slice(0, maxInt);
    const fracTrimmed = fracPart.slice(0, maxFrac);
    const result = cleaned.includes('.')
      ? `${intTrimmed}.${fracTrimmed}`
      : intTrimmed;
    setter(result);
    return;
  }

  const val = e.target.value.replace(',', '.');
  if (val === '' || decimalRegex(maxInt, maxFrac).test(val)) setter(val);
};