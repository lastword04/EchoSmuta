// baseQuery.js v2.1 (Фаза 2): единая обработка 401 для axios + RTK Query.
//
// ⚠️ НИЗКОУРОВНЕВЫЙ модуль: его импортируют axiosInstance.js и все RTK-слайсы.
// Импортировать сюда store ЗАПРЕЩЕНО: возникает цикл
// baseQuery → store/index → rootReducer → api-слайсы → baseQuery, и первый
// слайс, вовлечённый в цикл, падает с TDZ-ошибкой
// «Cannot access 'createAxiosBaseQuery' before initialization».
// Очистка persist-признаков входа при 401 выполняется слушателем события
// 'auth-error' в shared/store/index.js.

/**
 * Единая обработка 401 для ВСЕХ транспортов (axios-интерцептор и RTK Query).
 *
 * Разделение ответственности:
 *  - axiosInstance.createAuthInterceptor отвечает за refresh-цепочку и
 *    диспатчит window-событие 'auth-error' при провале refresh;
 *  - этот модуль ГАРАНТИРУЕТ очистку persist-признака входа
 *    (local.activeCharacterId / local.activeCharacterName) и ровно одно
 *    событие 'auth-error' даже при лавине параллельных 401 (типичный кейс:
 *    страница стреляет несколькими RTK Query запросами одновременно).
 *
 * Дедупликация: повторные вызовы в пределах AUTH_ERROR_DEDUPE_MS
 * игнорируются — защита от infinite loop / спама событий.
 */

const AUTH_ERROR_DEDUPE_MS = 100;
let lastAuthErrorAt = 0;

/**
 * Сообщает приложению об истёкшей авторизации.
 * @returns {boolean} true, если событие было отправлено этим вызовом.
 */
export function notifyAuthError() {
  const now = Date.now();
  if (now - lastAuthErrorAt < AUTH_ERROR_DEDUPE_MS) {
    return false; // кто-то рядом уже крикнул — не дублируем
  }
  lastAuthErrorAt = now;

  // Очистку persist-признаков входа (activeCharacterId / activeCharacterName /
  // userRole) выполняет слушатель 'auth-error' в shared/store/index.js —
  // он зарегистрирован один раз при создании стора и не зависит от того,
  // смонтирован ли ProtectedRoute. Прямой store.dispatch сюда тащить нельзя:
  // циклический импорт (см. шапку файла).

  window.dispatchEvent(new CustomEvent('auth-error'));
  return true;
}

/**
 * Универсальный декоратор: оборачивает любой baseQuery (fetchBaseQuery,
 * axiosBaseQuery и т.п.) и триггерит notifyAuthError() при 401.
 *
 * Пример для классического fetchBaseQuery:
 *   baseQuery: withAuthErrorHandler(fetchBaseQuery({ baseUrl: '/api' }))
 */
export const withAuthErrorHandler = (baseQuery) => async (args, api, extraOptions) => {
  const result = await baseQuery(args, api, extraOptions);
  if (result?.error?.status === 401) {
    notifyAuthError();
  }
  return result;
};

/**
 * Стандартная axios-baseQuery проекта.
 *
 * ⚠️ НАМЕРЕННО НЕ ОБРАБАТЫВАЕТ 401: этот baseQuery работает поверх
 * axios-инстансов, у которых уже стоит createAuthInterceptor
 * (axiosInstance.js). Интерцептор сам делает refresh → повтор запроса,
 * а при провале refresh вызывает notifyAuthError() (см. ниже) —
 * единая точка logout (Фаза 2). Дублирующая обработка 401 здесь
 * приводила к logout ДО завершения refresh-цепочки.
 *
 * Пример:
 *   baseQuery: createAxiosBaseQuery(characterApiInstance)
 *   baseQuery: createAxiosBaseQuery(economyApiInstance, { baseUrl: '/eco' })
 */
export const createAxiosBaseQuery =
  (instance, { baseUrl = '' } = {}) =>
  async (args) => {
    // RTK Query может передать либо строку (query: () => '/path'),
    // либо объект (query: () => ({ url: '/path', params: {...} })).
    // Нормализуем оба случая, чтобы старые слайсы (которые всегда возвращают
    // объект) продолжили работать как раньше, а новые админские (где
    // некоторые query возвращают строку) тоже заработали.
    const normalized = typeof args === 'string' ? { url: args } : (args || {});
    const { url, method = 'GET', params, ...restConfig } = normalized;
    const data = normalized.data ?? normalized.body;

    // Временный дебаг-блок
    if (String(url).includes('undefined')) {
      console.error('🚨 ОБНАРУЖЕН /undefined В URL:', baseUrl + url);
      console.trace('👇 СМОТРИ СТЕК ВЫЗОВОВ НИЖЕ:');
    }

    try {
      const result = await instance({
        url: baseUrl + url,
        method,
        data,
        params,
        ...restConfig,
      });
      return { data: result.data };
    } catch (axiosError) {
      return {
        error: {
          status: axiosError.response?.status,
          data: axiosError.response?.data || axiosError.message,
        },
      };
    }
  };
