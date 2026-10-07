import { authTokenApi } from "../../../entities/auth/api/authTokenApi";
import { storeRef } from "../../store/storeRef";
import { config } from "../../config/env/env";

export class DealsWebSocket {
  constructor(locationSlug, onDealEvent, onError, onClose, onReconnect) {
    this.locationSlug = locationSlug;
    this.onDealEvent = onDealEvent;
    this.onError = onError;
    this.onClose = onClose;
    this.onReconnect = onReconnect;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.manualClose = false;
    this.isDisconnecting = false;
  }

  async connect() {
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

      this.manualClose = false;
      this.isDisconnecting = false;

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
      // и каждое событие сделки доставляется дважды.
      if (this.manualClose || this.isDisconnecting) {
        return;
      }

      const wsUrl = `${config.CHAT_WS_BASE_URL}deals?token=${token}&location_slug=${this.locationSlug}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        const isReconnect = this.reconnectAttempts > 0;
        this.reconnectAttempts = 0;
        this.isDisconnecting = false;
        if (isReconnect) {
          this.onReconnect?.();
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.onDealEvent(message);
        } catch {
          // тихо
        }
      };

      this.ws.onerror = (error) => {
        if (this.isDisconnecting || this.manualClose) return;
        this.onError?.(error);
      };

      this.ws.onclose = (event) => {
        const wsRef = this.ws;
        this.ws = null;
        this.onClose?.(event);

        if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
          }, this.reconnectInterval);
        }

        if (wsRef) {
          wsRef.onopen = null;
          wsRef.onerror = null;
          wsRef.onclose = null;
          wsRef.onmessage = null;
        }
      };
    } catch (error) {
      this.onError?.(error);
    }
  }

  disconnect() {
    this.manualClose = true;
    this.isDisconnecting = true;

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.close();
        } catch {
          // тихо
        }
      }
      this.ws.onopen = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
      this.ws.onmessage = null;
      this.ws = null;
    }
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}