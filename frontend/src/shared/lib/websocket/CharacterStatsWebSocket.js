import { authTokenApi } from "../../../entities/auth/api/authTokenApi";
import { storeRef } from "../../store/storeRef";
import { config } from "../../config/env/env";

export class CharacterStatsWebSocket {
  constructor(characterId, onStatsUpdate, onError, onClose, onReconnect) {
    this.characterId = characterId;
    this.onStatsUpdate = onStatsUpdate;
    this.onError = onError;
    this.onClose = onClose;
    this.onReconnect = onReconnect;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 5000;
    this.manualClose = false;
    this.isDisconnecting = false;
    this.hasConnectedOnce = false;
    this.reconnectTimer = null;
  }

  async connect() {
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
      if (this.ws && this.ws.readyState === WebSocket.CONNECTING) return;

      this.manualClose = false;
      this.isDisconnecting = false;

      const tokenData = await storeRef.current
        .dispatch(authTokenApi.endpoints.getToken.initiate(undefined, { forceRefetch: true }))
        .unwrap();
      const token = tokenData.token;

      if (!token) {
        throw new Error('No access token received');
      }

      const baseUrl = config.CHARACTER_API_BASE_URL
        .replace('http://', 'ws://')
        .replace('https://', 'wss://')
        .replace('/api/characters', '');

      const wsUrl = `${baseUrl}/ws/character/${this.characterId}/stats?token=${token}`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.isDisconnecting = false;

        // Вызываем onReconnect только при повторном подключении (не при первом)
        if (this.hasConnectedOnce) {
          this.onReconnect?.();
        }
        this.hasConnectedOnce = true;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onStatsUpdate(data);
        } catch (error) {
          console.error('[CharacterStatsWS] Parse error:', error);
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
          this.reconnectTimer = setTimeout(() => {
            if (this.manualClose) return;
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

      // Реконнект-цикл не должен обрываться, если фейлнулся getToken
      // (сеть ещё не вернулась): планируем повторную попытку
      if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectTimer = setTimeout(() => {
          if (this.manualClose) return;
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectInterval);
      }
    }
  }

  disconnect() {
    this.manualClose = true;
    this.isDisconnecting = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        try {
          this.ws.close();
        } catch {
          // ignore
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