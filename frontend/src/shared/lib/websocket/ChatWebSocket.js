import { authTokenApi } from "../../../entities/auth/api/authTokenApi";
import { storeRef } from "../../store/storeRef";
import { config } from "../../config/env/env";

export class ChatWebSocket {
  constructor(room, locationSlug, onMessage, onError, onClose, onReconnect) {
    this.room = room;
    this.locationSlug = locationSlug;
    this.onMessage = onMessage;
    this.onError = onError;
    this.onClose = onClose;
    this.onReconnect = onReconnect;
    this.wasConnected = false;
    this.ws = null;
    this.reconnectAttempts = 0; // счётчик попыток: растёт, участвует в backoff
    this.reconnectInterval = 1000; // база backoff: 1с → 2с → 4с → ... кап 60с
    this.manualClose = false;
    this.isDisconnecting = false;
  }

  async connect() {
    try {
      if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;

      this.manualClose = false;
      this.isDisconnecting = false; // ← Сбрасываем флаг

      // Поколение вызова connect(): защищает от двойного создания сокета,
      // если connect() вызывается повторно, пока предыдущий ещё ждёт токен.
      this.connectGeneration = (this.connectGeneration || 0) + 1;
      const generation = this.connectGeneration;

      const tokenData = await storeRef.current
        .dispatch(authTokenApi.endpoints.getToken.initiate(undefined, { forceRefetch: true }))
        .unwrap();
      const token = tokenData.token;

      if (!token) {
        throw new Error('No access token received');
      }

      // Повторная проверка ПОСЛЕ await: пока ждали токен, мог быть вызван
      // disconnect() (StrictMode double-mount, HMR, быстрая смена персонажа).
      // Без этой проверки открывается "зомби"-сокет, который никто не закроет,
      // и каждое сообщение чата доставляется дважды.
      if (this.manualClose || this.isDisconnecting || generation !== this.connectGeneration) {
        return;
      }

      let wsUrl = `${config.CHAT_WS_BASE_URL}${this.room}?token=${token}`;
      if (this.locationSlug) {
        wsUrl = `${wsUrl}&location_slug=${this.locationSlug}`;
      }
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`WebSocket connected to room: ${this.room}`);
        this.reconnectAttempts = 0;
        this.isDisconnecting = false;
        // Ресинк: переподключение ПОСЛЕ обрыва. События за время обрыва
        // потеряны (pub/sub без истории) — клиент должен перезачитать состояние.
        if (this.wasConnected && this.onReconnect) {
          this.onReconnect();
        }
        this.wasConnected = true;
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);               

          // ✅ ПЕРЕХВАТ ТЕХНИЧЕСКОГО СОБЫТИЯ экономики (все действия, не только deal_completed)
          if (message?.event_type === 'economy_state_updated') {
            const data = message.data || {};
            const action = data.action;
            
            // Формируем detail для всех типов событий
            const detail = {
              action: action,
              location_slug: data.location_slug,
              initiator_character_id: data.initiator_character_id,
              partner_character_id: data.partner_character_id,
              lot_id: data.lot_id,
              shop_id: data.shop_id,
              inventory_item_id: data.inventory_item_id,
              item_id: data.item_id,
              message: data.message,   
              result_status: data.result_status,
              item_slug: data.item_slug,
              target_user_ids: data.partner_character_id 
                ? [data.initiator_character_id, data.partner_character_id]  // Для сделок
                : []  // Для действий с лавкой — всем в локации
            };
            
            window.dispatchEvent(new CustomEvent('economy-updated', { detail }));
            
            // ⚠️ КРИТИЧЕСКИ ВАЖНО: прерываем выполнение. Сообщение НЕ пойдет в this.onMessage и НЕ попадет в чат.
            return;
          }

          // ✅ Обработка события состояния дома
          if (message?.event_type === 'house_state_updated') {
            const data = message.data || {};
            const detail = {
                action: data.action,
                house_id: data.house_id,
                affected_character_id: data.affected_character_id || null,
                house_payload: data.house_payload || null,
            };
            window.dispatchEvent(new CustomEvent('house-updated', { detail }));
            return;
          }

          if (message?.event_type === 'rest_state_updated') {
            const data = message.data || {};
            window.dispatchEvent(new CustomEvent('rest-updated', {
              detail: { location_slug: data.location_slug },
            }));
            return;
          }
          
          if (message?.event_type === 'banned') {
            console.log('User banned, triggering logout');
            // Отправляем глобальное событие для React компонентов
            window.dispatchEvent(new CustomEvent('user-banned', { 
              detail: { message: message.message || 'Вы забанены администратором' } 
            }));
            return; // Не передаём дальше
          }

          // Если пришло событие завершения крафта — уведомляем WorkshopView
          if (message?.event_type === 'crafting_stage_result') {
            window.dispatchEvent(new CustomEvent('crafting-stage-result', { detail: message }));
          }
         
          if (message?.event_type === 'new_mail') {
            window.dispatchEvent(new CustomEvent('mail-notification', { detail: message }));
            return; // Не передавать в чат — это техническое уведомление, а не сообщение
          }

          // Presence события (вход/выход/смена локации)
          // ═══ ДОГОВОР ДЛЯ ВСЕХ СЛУШАТЕЛЕЙ presence-event ═══
          // Поток содержит события ОБО ВСЕХ персонажах, включая самого себя.
          // Каждый addEventListener('presence-event') ОБЯЗАН первым делом проверить:
          //   if (character_id === character?.id) return;
          // История: пропущенный фильтр в useDealsLogic давал свой ник в списке партнёров.
          // Линт-правило no-restricted-syntax принудительно требует подтверждения (eslint-disable-line).
          if (message?.event_type === 'character_online' || message?.event_type === 'character_location') {
            window.dispatchEvent(new CustomEvent('presence-event', { detail: message }));
            return;
          }

          this.onMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        // 🔑 ИГНОРИРУЕМ ошибки при отключении
        if (this.isDisconnecting || this.manualClose) {
          console.log('WebSocket error ignored (disconnecting)');
          return;
        }
        console.error('WebSocket error:', error);
        this.onError?.(error);
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);

        // Не переподключаем при дедупликации сервером
        if (event.code === 1000 && event.reason === 'Duplicate connection') {
            console.log('Connection closed by server (duplicate), not reconnecting');
            this.manualClose = true;
        }
        
        // Очищаем ссылку
        const wsRef = this.ws;
        this.ws = null;
        
        this.onClose?.(event);

        // Не переподключаем при ручном закрытии.
        // Лимита попыток нет: сервер может подниматься минуты (деплой) —
        // соединение должно восстановиться само. Пауза растёт экспоненциально
        // (1с → 2с → ... ) с капом 60с, чтобы не долбить лежащий сервер.
        if (!this.manualClose) {
          const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts), 60000);
          setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
          }, delay);
        }
        
        // Очищаем обработчики
        if (wsRef) {
          wsRef.onopen = null;
          wsRef.onerror = null;
          wsRef.onclose = null;
          wsRef.onmessage = null;
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.onError?.(error);
    }
  }

  send(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect() {
    this.manualClose = true;
    this.isDisconnecting = true; // ← Устанавливаем ПЕРЕД закрытием
    
    if (this.ws) {
      // 🔑 Проверяем состояние перед закрытием
      if (this.ws.readyState === WebSocket.CONNECTING) {
        // Сокет ещё подключается — отменяем рукопожатие, иначе он
        // всё равно откроется на сервере и останется "зомби"-сокетом.
        console.log('WebSocket was still connecting, closing...');
        try {
          this.ws.close();
        } catch (e) {
          console.warn('WebSocket close error (ignored):', e);
        }
      } else if (this.ws.readyState === WebSocket.OPEN) {
        // Сокет открыт — закрываем
        try {
          this.ws.close();
        } catch (e) {
          console.warn('WebSocket close error (ignored):', e);
        }
      }
      
      // Очищаем обработчики
      this.ws.onopen = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
      this.ws.onmessage = null;
      
      this.ws = null;
      console.log('WebSocket manually disconnected');
    }
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
