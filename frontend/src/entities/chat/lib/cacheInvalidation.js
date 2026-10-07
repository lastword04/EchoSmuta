// entities/chat/lib/cacheInvalidation.js
import { chatApi } from '../api/chatApi';

/**
 * Централизованная инвалидация кэшей чата.
 * 
 * Вместо вызова `dispatch(chatApi.util.invalidateTags([...]))` в разных местах,
 * используйте эту функцию — она знает какие теги инвалидировать.
 * 
 * @param {Function} dispatch - Redux dispatch
 * @param {Object} options - Опции инвалидации
 * @param {boolean} options.history - Инвалидировать историю чата
 * @param {string} [options.historyRoom] - Конкретная комната ('global', 'location:slug', или undefined для всех)
 * @param {boolean} options.onlineUsers - Инвалидировать списки онлайна
 * @param {string[]} [options.locations] - Конкретные локации для онлайна
 */
export const invalidateChatCache = (dispatch, options = {}) => {
  const tags = [];
  
  if (options.history) {
    if (options.historyRoom) {
      tags.push({ type: 'ChatHistory', id: options.historyRoom });
    } else {
      // Инвалидируем ВСЮ историю (обе вкладки, все комнаты)
      tags.push('ChatHistory');
    }
  }
  
  if (options.onlineUsers) {
    // Глобальный онлайн всегда инвалидируется
    tags.push({ type: 'OnlineUsers', id: 'global' });
    
    // Конкретные локации если указаны
    if (options.locations?.length) {
      options.locations.forEach(location => {
        tags.push({ type: 'OnlineUsers', id: location });
      });
    }
  }
  
  if (tags.length > 0) {
    dispatch(chatApi.util.invalidateTags(tags));
  }
};

/**
 * Хелпер для обновления данных в кэше (альтернатива инвалидации)
 * Используется когда нужно оптимистично обновить данные без сетевых запросов
 */
export const updateChatCache = (dispatch, options = {}) => {
  if (options.onlineUsers) {
    if (options.updateGlobal) {
      dispatch(
        chatApi.util.updateQueryData(
          'getOnlineCharacters',
          { locationSlug: null, limit: 50, offset: 0 },
          options.updateGlobal
        )
      );
    }
    
    if (options.updateLocations) {
      options.updateLocations.forEach(({ location, updater }) => {
        dispatch(
          chatApi.util.updateQueryData(
            'getOnlineCharacters',
            { locationSlug: location, limit: 50, offset: 0 },
            updater
          )
        );
      });
    }
  }
};