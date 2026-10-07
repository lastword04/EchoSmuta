/**
 * Парсит дату с бэка как UTC.
 * Обрабатывает:
 * - ISO-строки без таймзоны ("2026-09-17T10:04:07")
 * - ISO-строки с таймзоной ("2026-09-17T10:04:07Z")
 * - Unix timestamp в секундах (1758268800)
 * - Unix timestamp в миллисекундах (1758268800000)
 */
export const parseUtcDate = (value) => {
  if (!value) return null;
  
  // Если число — это Unix timestamp
  if (typeof value === 'number') {
    // Если меньше 10^12, это секунды, иначе миллисекунды
    const ms = value < 1e12 ? value * 1000 : value;
    return new Date(ms);
  }
  
  // Если строка
  const s = String(value);
  return new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z');
};