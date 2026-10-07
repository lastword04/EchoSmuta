// Маппинг слов для разных типов лавок (с правильным родом)
const SHOP_TYPE_MAP = {
  '1.9.pharmacy': 'вашей аптеке',
  '1.21.furniture-shop': 'вашей мебельной лавке',
  '1.22.hunting-shop': 'вашей охотничьей лавке',
  '1.24.bird-market': 'вашем питомнике',
  '1.25.fish-shop': 'вашей рыбной лавке',
  '1.27.trade-hall': 'вашей палатке',
};

export function getErrorMessage(e, fallback = "Произошла ошибка") {
  const data = e?.data ?? e?.response?.data;
  const errorCode = data?.error_code;  // ✅ НУЖНО: для проверки типа ошибки
  const extras = data?.extras || {};   // ✅ НУЖНО: для получения location_slug

  // Проверка вместимости лавки
  if (errorCode === 'SHOP_CAPACITY_EXCEEDED') {
    const locationSlug = extras.location_slug;  // ← используем extras
    const shopType = SHOP_TYPE_MAP[locationSlug] || 'вашей лавке';
    return `В ${shopType} нет места`;
  }

  // Проверка веса персонажа
  if (errorCode === 'CHARACTER_WEIGHT_EXCEEDED') {
    return 'У вас нет места в рюкзаке';
  }

  // Стандартная логика для остальных ошибок
  if (typeof data === "string" && data) return data;
  // Чистое сообщение валидации (ValidationError кладёт его в extras.message) —
  // раньше detail показывался с префиксом "Validation error in field: ..."
  if (typeof data?.extras?.message === "string" && data.extras.message) return data.extras.message;
  if (typeof data?.detail === "string" && data.detail) return data.detail;
  if (typeof data?.message === "string" && data.message) return data.message;

  return fallback;
}