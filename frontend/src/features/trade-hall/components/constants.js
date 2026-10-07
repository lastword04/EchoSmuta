// ==========================================
// DEAL STATUS CONSTANTS
// ==========================================

export const DEAL_STATUS = {
  DRAFT: 'DRAFT',
  ACTIVE: 'ACTIVE',
  COMPLETED: 'COMPLETED',
  CANCELLED: 'CANCELLED',
  EXPIRED: 'EXPIRED',
};

export const FINAL_DEAL_STATUSES = new Set([
  DEAL_STATUS.COMPLETED,
  DEAL_STATUS.CANCELLED,
  DEAL_STATUS.EXPIRED,
]);

// ==========================================
// ALLOWED LOCATIONS
// ==========================================

export const DEAL_ALLOWED_LOCATIONS = new Set([
  '1.13.forge',
  '1.16.jewelers',
]);

// ==========================================
// ERROR TEXTS
// ==========================================

export const DEAL_ERROR_TEXTS = {
  DEAL_PARTNER_OFFLINE: "Персонаж оффлайн",
  DEAL_PARTNER_DEPARTED: "Персонаж ушел",
  DEAL_NOT_READY: "Не все стороны готовы к сделке",
  DEAL_BOTH_SIDES_MONEY: "Только одна сторона может выставить деньги в сделку",
  DEAL_EMPTY_OFFER: "Ваше предложение пусто",
  INSUFFICIENT_FUNDS: "Недостаточно средств",
  DEAL_ASSET_UNAVAILABLE: "Предмет не найден или недоступен для сделки (надет, в лавке, на продаже или уже в другой сделке)",
  "Insufficient available resource amount": "Недостаточно ресурсов",
  "Deal item not found in your offer": "Этого предмета уже нет в вашем предложении",
  "Resource is not present in your offer": "Этого ресурса уже нет в вашем предложении",
  DEAL_SELF_WEIGHT_LIMIT: "У вас нет места в рюкзаке",
  DEAL_PARTNER_WEIGHT_LIMIT: "У партнёра по сделке нет места в рюкзаке",
  DEAL_MIXED_OFFER: "Одна сторона сделки может предлагать только деньги или только товары",
  DEAL_BOTH_SIDES_GOODS: "Товары в сделку может добавлять только одна сторона",
  DEAL_NO_MONEY_SIDE: "Одна из сторон должна добавить деньги в сделку",
  DEAL_PRICE_TOO_LOW: "Цена ниже половины стоимости товаров",
  // --- Редкие английские deal-ошибки: русский текст по error_code (fallback) ---
  DEAL_NOT_FOUND: "Сделка не найдена",
  DEAL_ACCESS_DENIED: "Нет доступа к этой сделке",
  DEAL_PROXIMITY_REQUIRED: "Партнёр слишком далеко — вы должны быть в одной локации",
  DEAL_INVALID_STATE: "Сделка не может быть изменена (уже завершена или недоступна)",
  DEAL_SELF_PARTNER: "Нельзя создать сделку с самим собой",
  DEAL_COMPLETION_FAILED: "Не удалось завершить сделку",
  DEAL_GOLD_TRADE_DISABLED: "Для торговли золотом нужна лицензия торговца",
};