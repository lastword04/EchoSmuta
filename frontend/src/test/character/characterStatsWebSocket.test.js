// NOTE: test → shared/entities import допустим для интеграционных тестов транспорта
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Управляемый ответ getToken. Через vi.hoisted, т.к. vi.mock хойстится.
const hoisted = vi.hoisted(() => ({ token: { value: { token: 'test-token' } } }));

vi.mock('../../entities/auth/api/authTokenApi', () => ({
  authTokenApi: {
    endpoints: {
      getToken: {
        initiate: () => ({
          unwrap: () =>
            hoisted.token.value.error
              ? Promise.reject(hoisted.token.value.error)
              : Promise.resolve(hoisted.token.value),
        }),
      },
    },
  },
}));

// storeRef.current.dispatch для connect(): возвращаем action как есть —
// mock-инициатор уже несёт .unwrap().
vi.mock('../../shared/store/storeRef', () => ({
  storeRef: { current: { dispatch: (action) => action } },
}));

vi.mock('../../shared/config/env/env', () => ({
  config: { CHARACTER_API_BASE_URL: 'http://localhost:8082/api/characters' },
}));

import { CharacterStatsWebSocket } from '../../shared/lib/websocket/CharacterStatsWebSocket';

const RECONNECT_MS = 5000;

class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances = [];

  constructor(url) {
    this.url = url;
    this.readyState = FakeWebSocket.CONNECTING;
    FakeWebSocket.instances.push(this);
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  serverClose(code = 1006) {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.({ code, reason: '' });
  }

  close() {
    this.readyState = FakeWebSocket.CLOSED;
  }
}

const flush = () => vi.advanceTimersByTimeAsync(0);

describe('CharacterStatsWebSocket (reconnect + self-healing hooks)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeWebSocket.instances = [];
    globalThis.WebSocket = FakeWebSocket;
    hoisted.token.value = { token: 'test-token' };
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    delete globalThis.WebSocket;
  });

  it('onReconnect НЕ вызывается на первом connect', async () => {
    const onReconnect = vi.fn();
    const sock = new CharacterStatsWebSocket(1, vi.fn(), vi.fn(), vi.fn(), onReconnect);

    await sock.connect();
    expect(FakeWebSocket.instances).toHaveLength(1);

    FakeWebSocket.instances[0].open();
    expect(onReconnect).not.toHaveBeenCalled();
  });

  it('onReconnect вызывается ровно один раз при реконнекте после обрыва', async () => {
    const onReconnect = vi.fn();
    const sock = new CharacterStatsWebSocket(1, vi.fn(), vi.fn(), vi.fn(), onReconnect);

    await sock.connect();
    FakeWebSocket.instances[0].open();

    FakeWebSocket.instances[0].serverClose();        // планирует реконнект
    await vi.advanceTimersByTimeAsync(RECONNECT_MS); // таймер сработал → новый connect
    await flush();

    expect(FakeWebSocket.instances).toHaveLength(2);
    expect(onReconnect).not.toHaveBeenCalled();      // сокет ещё не открыт

    FakeWebSocket.instances[1].open();
    expect(onReconnect).toHaveBeenCalledTimes(1);
  });

  it('disconnect() во время ожидания реконнекта не даёт открыть новый сокет', async () => {
    const sock = new CharacterStatsWebSocket(1, vi.fn(), vi.fn(), vi.fn(), vi.fn());

    await sock.connect();
    FakeWebSocket.instances[0].open();

    FakeWebSocket.instances[0].serverClose(); // таймер реконнекта запланирован
    sock.disconnect();                        // manualClose = true

    await vi.advanceTimersByTimeAsync(RECONNECT_MS * 2);
    await flush();

    expect(sock.manualClose).toBe(true);
    expect(FakeWebSocket.instances).toHaveLength(1); // новый сокет не создан
  });

  it('фейл getToken на старте планирует реконнект и восстанавливается', async () => {
    hoisted.token.value = { error: new Error('network down') };
    const onError = vi.fn();
    const sock = new CharacterStatsWebSocket(1, vi.fn(), onError, vi.fn(), vi.fn());

    await sock.connect();
    expect(onError).toHaveBeenCalledTimes(1);
    expect(FakeWebSocket.instances).toHaveLength(0);

    // сеть вернулась — реконнект-цикл должен подняться сам
    hoisted.token.value = { token: 'test-token' };
    await vi.advanceTimersByTimeAsync(RECONNECT_MS);
    await flush();

    expect(sock.reconnectAttempts).toBe(1);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it('getToken-фейл + disconnect() не создаёт сокет после таймера', async () => {
    hoisted.token.value = { error: new Error('network down') };
    const sock = new CharacterStatsWebSocket(1, vi.fn(), vi.fn(), vi.fn(), vi.fn());

    await sock.connect();
    sock.disconnect();
    await vi.advanceTimersByTimeAsync(RECONNECT_MS * 2);
    await flush();

    expect(FakeWebSocket.instances).toHaveLength(0);
  });

  it('onmessage парсит JSON → onStatsUpdate; onerror пробрасывается; isConnected корректен', async () => {
    const onStatsUpdate = vi.fn();
    const onError = vi.fn();
    const sock = new CharacterStatsWebSocket(1, onStatsUpdate, onError, vi.fn(), vi.fn());

    await sock.connect();
    const ws = FakeWebSocket.instances[0];
    ws.open();

    ws.onmessage({ data: JSON.stringify({ event: 'stats_updated', health: 7 }) });
    expect(onStatsUpdate).toHaveBeenCalledWith({ event: 'stats_updated', health: 7 });

    ws.onerror(new Error('boom'));
    expect(onError).toHaveBeenCalledTimes(1);

    expect(sock.isConnected()).toBe(true);
  });
});
