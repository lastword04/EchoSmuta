import { addMessageToChatHistory } from '../api/chatApi';
import { restApi } from '../../character/api/restApi';
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';

/**
 * Роутинг входящего сообщения чата по RTK-кэшам.
 * 
 * Правила раскладки (должны совпадать с тем, как ChatPanel запрашивает историю):
 *   Общий:   {room:'global', locationSlug: filter ? L : null}
 *   Локация: {room:L,        locationSlug: filter ? L : null}
 * 
 * Чистая функция домена чата. Инфраструктура сокета (звуки, обработка
 * ошибок сервера) живёт в ChatWebSocketProvider и не должна сюда попадать.
 */
export const routeMessageToCaches = (dispatch, { message, character, settings }) => {
  const newMessage = {
    id: message.id,
    time: message.created_at
      ? parseUtcDate(message.created_at).toLocaleTimeString('ru-RU', {
          hour: '2-digit', minute: '2-digit',
        })
      : '',
    user: message.sender_name,
    user_id: message.sender_id,
    text: message.content,
    message_type: message.message_type,
    room: message.room,
    is_trade: message.is_trade,
    target_user_ids: message.target_user_ids || [],
    target_user_names: message.target_user_names || [],
  };

  const L = character.location_slug;
  const filterOn = settings.filter_location_messages;

  if (message.room === 'private' || message.room === 'system') {
    // Приватные и системные — в ОБЕ вкладки (Общий и Локация).
    // Дедупликация по id внутри addMessageToChatHistory защищает от дублей.
    addMessageToChatHistory(dispatch, {
      room: 'global',
      locationSlug: filterOn ? L : null,
      message: newMessage,
    });
    if (L) {
      addMessageToChatHistory(dispatch, {
        room: L,
        locationSlug: filterOn ? L : null,
        message: newMessage,
      });
    }

    // Системка истечения аренды — инвалидируем Rest
    if (
      message.room === 'system' &&
      message.message_type === 'system_private' &&
      message.content?.includes('Время аренды комнаты')
    ) {
      dispatch(restApi.util.invalidateTags(['Rest']));
    }
  } else if (message.room === 'global') {
    addMessageToChatHistory(dispatch, {
      room: 'global',
      locationSlug: filterOn ? L : null,
      message: newMessage,
    });
  } else {
    // Локационное: всегда в кэш вкладки «Локация»
    addMessageToChatHistory(dispatch, {
      room: message.room,
      locationSlug: filterOn ? message.room : null,
      message: newMessage,
    });
    // При filter=true вкладка «Общий» тоже показывает локацию
    if (filterOn) {
      addMessageToChatHistory(dispatch, {
        room: 'global',
        locationSlug: L,
        message: newMessage,
      });
    }
  }
};