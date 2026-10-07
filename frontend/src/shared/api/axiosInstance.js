import axios from 'axios';
import { config } from '../config/env/env';
import { notifyAuthError } from './baseQuery';

// --- Создание инстансов ---
export const apiInstance = axios.create({
  withCredentials: true,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

export const authApiInstance = axios.create({
  baseURL: config.API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const authProtectedApiInstance = axios.create({
  baseURL: config.API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});


export const characterApiInstance = axios.create({
  baseURL: config.CHARACTER_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const statsApiInstance = axios.create({
  baseURL: config.STATS_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const restApiInstance = axios.create({
  baseURL: config.REST_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const housesApiInstance = axios.create({
  baseURL: config.HOUSES_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const currencyApiInstance = axios.create({
  baseURL: config.CURRENCY_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const notebookApiInstance = axios.create({
  baseURL: config.NOTEBOOK_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const panelApiInstance = axios.create({
  baseURL: config.PANEL_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const fileApiInstance = axios.create({
  baseURL: config.FILE_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const captchaApiInstance = axios.create({
  baseURL: config.CAPTCHA_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const forumApiInstance = axios.create({
  baseURL: config.FORUM_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const chatApiInstance = axios.create({
  baseURL: config.CHAT_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});

export const mailApiInstance = axios.create({
  baseURL: config.MAIL_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
})

export const categoryApiInstance = axios.create({
  baseURL: config.CATEGORY_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
})

export const visitApiInstance = axios.create({
  baseURL: config.VISIT_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
})

export const resourceApiInstance = axios.create({
  baseURL: config.RESOURCE_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
})

export const itemApiInstance = axios.create({
  baseURL: config.ITEM_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
})

export const miningApiInstance = axios.create({
  baseURL: config.MINING_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
})

export const economyApiInstance = axios.create({
  baseURL: config.ECONOMY_API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },
});



// --- Управление refresh ---
let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback);
};

const onRefreshed = (newToken) => {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
};

const onRefreshFailed = (err) => {
  refreshSubscribers.forEach((callback) => callback(null, err));
  refreshSubscribers = [];
};

const refreshToken = async () => {
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      subscribeTokenRefresh((token, err) => (err ? reject(err) : resolve(token)));
    });
  }

  isRefreshing = true;

  try {
    const response = await authApiInstance.post('/refresh');
    const newToken = response.data.access_token;

    onRefreshed(newToken);
    return newToken;

  } catch (error) {
    // warn вместо error: провал refresh — штатный сценарий на публичных страницах
    // (например, HomePage после полного выхода из аккаунта), а не авария.
    console.warn('Refresh skipped: not authenticated');
    onRefreshFailed(error);   // ← ВОТ ЭТА СТРОКА чинит висение
    // Единая точка logout (Фаза 2): очистка persist-признака входа
    // + одно window-событие 'auth-error' с дедупликацией.
    notifyAuthError();
    throw error;
  } finally {
    isRefreshing = false;
  }
};

// --- Единый интерцептор ---
const createAuthInterceptor = (apiInstance) => {
  apiInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      // Если запрос помечен как "не повторять при 401"
      if (originalRequest.skipAuthRetry) {
        return Promise.reject(error);
      }

      // Ретраим ТОЛЬКО 401. 403 = "нет прав / не в игре" — ретрай бесполезен
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        if (originalRequest.url?.endsWith('/refresh')) {
          notifyAuthError();
          return Promise.reject(error);
        }

        try {
          await refreshToken();
          return apiInstance(originalRequest);
        } catch (refreshError) {
          notifyAuthError();
          return Promise.reject(refreshError);
        }
      }

      // 403 CHARACTER_NOT_ONLINE — персонаж не в игре, возвращаем на выбор персонажа
      if (
        error.response?.status === 403 &&
        error.response?.data?.error_code === 'CHARACTER_NOT_ONLINE'
      ) {
        window.dispatchEvent(
          new CustomEvent('character-not-online', { detail: error.response.data })
        );
      }

      return Promise.reject(error);
    }
  );
};

// --- Применяем интерцепторы ко всем инстансам ---
createAuthInterceptor(apiInstance);
createAuthInterceptor(visitApiInstance);
createAuthInterceptor(authProtectedApiInstance);
createAuthInterceptor(characterApiInstance);
createAuthInterceptor(statsApiInstance);
createAuthInterceptor(currencyApiInstance);
createAuthInterceptor(notebookApiInstance);
createAuthInterceptor(panelApiInstance);
createAuthInterceptor(fileApiInstance);
createAuthInterceptor(forumApiInstance);
createAuthInterceptor(chatApiInstance);
createAuthInterceptor(mailApiInstance);
createAuthInterceptor(categoryApiInstance);
createAuthInterceptor(resourceApiInstance);
createAuthInterceptor(itemApiInstance);
createAuthInterceptor(miningApiInstance);
createAuthInterceptor(economyApiInstance);
createAuthInterceptor(restApiInstance);
createAuthInterceptor(housesApiInstance);

export {
  refreshToken, // если понадобится вызывать вручную
};
