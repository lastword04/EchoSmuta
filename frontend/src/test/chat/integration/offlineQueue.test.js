// NOTE: test → app import is acceptable for integration tests
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import { render, act } from '@testing-library/react';
import { Provider } from 'react-redux';

// Мокаем ТОЛЬКО транспортный класс и сеть. offlineQueue и ChatWebSocketProvider — реальный код.
const wsInstances = [];
let nextSocketConnected = false; // тест говорит, подключится ли следующий сокет
vi.mock('../../../shared/lib/websocket/ChatWebSocket', () => ({
  ChatWebSocket: class MockChatWebSocket {
    constructor(room, locationSlug, onMessage, onError) {
      this.room = room;
      this.locationSlug = locationSlug;
      this.onMessage = onMessage;
      this.onError = onError;
      this.connected = nextSocketConnected;
      this.sentMessages = [];
      wsInstances.push(this);
    }
    async connect() {
      // Сокет реально НЕ подключён, пока тест не «откроет» его вручную
      await Promise.resolve();
    }
    isConnected() {
      return this.connected;
    }
    send(message) {
      if (this.connected) {
        this.sentMessages.push(message);
        return true;
      }
      return false;
    }
    disconnect() {
      this.connected = false;
    }
  },
}));

vi.mock('../../../entities/auth/api/authTokenApi', () => ({
  // ChatWebSocket.connect() при подключении диспатчит getToken через storeRef.
  // storeRef в тестовом окружении пустой (null), поэтому стабим весь модуль —
  // тесты offline-очереди не зависят от получения токена.
  authTokenApi: { endpoints: { getToken: { initiate: vi.fn(() => ({ type: 'mock/getToken' })) } } },
}));

vi.mock('../../../shared/api/axiosInstance', () => ({
  chatApiInstance: vi.fn(async () => ({ data: { chat_enabled: true } })),
  characterApiInstance: vi.fn(async () => ({ data: {} })),
  // Цепочка импортов: тест мокает транспортный класс ChatWebSocket, но реальный
  // модуль shared/lib/websocket/ChatWebSocket всё равно загружается, а он тянет
  // entities/auth/api/authTokenApi → тот на уровне модуля требует
  // authProtectedApiInstance (createAxiosBaseQuery). Достаточно объекта-заглушки:
  // по нему вызывается только createAxiosBaseQuery, сетевых запросов тест не делает.
  authProtectedApiInstance: {},
  // Аналогично для entities/character/api/restApi, который импортирует
  // ChatWebSocketProvider (реакция на system-сообщение об истечении аренды) —
  // на уровне модуля restApi требует restApiInstance через createAxiosBaseQuery.
  restApiInstance: {},
}));

import { ErrorProvider } from '../../../shared/lib/context/ErrorContext';
import { ChatWebSocketProvider } from '../../../app/providers/hooks/useGlobalWebSocket';
import { useChatSend } from '../../../entities/chat/hooks/useChatSend';
import { chatApi } from '../../../entities/chat/api/chatApi';
import { addToOfflineQueue, flushOfflineQueue, getQueueSize } from '../../../entities/chat/lib/offlineQueue';

const createTestStore = () =>
  configureStore({
    reducer: {
      [chatApi.reducerPath]: chatApi.reducer,
      session: () => ({ activeTab: 'global' }), // селектор провайдера: state.session.activeTab
    },
    middleware: (getDefault) => getDefault().concat(chatApi.middleware),
  });

const CHARACTER = { id: 1, location_slug: 'forest' };

// Дочерний компонент вытаскивает send из контекста провайдера
let sendFn = null;
const TestChild = () => {
  sendFn = useChatSend();
  return null;
};

const buildTree = (store) =>
  React.createElement(
    Provider,
    { store },
    React.createElement(
      ErrorProvider,
      null,
      React.createElement(
        ChatWebSocketProvider,
        { character: CHARACTER },
        React.createElement(TestChild)
      )
    )
  );

// Провайдер кладёт в контекст sendRef.current на момент рендера, поэтому после
// маунт-эффектов нужен rerender, чтобы TestChild захватил уже подключённый send
const mountProvider = (store) => render(buildTree(store));

beforeEach(() => {
  wsInstances.length = 0;
  sendFn = null;
  nextSocketConnected = false;
  vi.clearAllMocks();
  flushOfflineQueue(); // очередь — модульный синглтон, чистим между тестами
});

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
});

describe('Integration: offline queue + ChatWebSocketProvider', () => {
  beforeEach(() => {
    // Провайдер создаёт Audio в эффекте — jsdom не умеет играть звук, стабим
    vi.stubGlobal('Audio', class {
      constructor() {
        this.currentTime = 0;
        this.play = vi.fn().mockResolvedValue(undefined);
      }
    });
  });

  it('сокет не подключён → сообщение сохраняется в очередь, отправка возвращает false', async () => {
    const store = createTestStore();
    const mounted = mountProvider(store);
    await act(async () => {});
    await act(async () => {});
    mounted.rerender(buildTree(store)); // захватить реальный sendRef из контекста

    const socket = wsInstances[0];
    socket.connected = false; // соединения нет

    let result;
    act(() => {
      result = sendFn({ text: 'offline msg' });
    });

    expect(result).toBe(false); // отправка не удалась
    expect(getQueueSize()).toBe(1); // сообщение легло в реальную очередь
    expect(socket.sentMessages).toHaveLength(0); // в сокет ничего не ушло

    // Ещё одно сообщение — очередь растёт
    act(() => {
      result = sendFn({ text: 'second' });
    });
    expect(result).toBe(false);
    expect(getQueueSize()).toBe(2);

    mounted.unmount();
  });

  it('сокет подключился → очередь очистилась и сообщения ушли в сокет', async () => {
    // Сначала копим очередь как в «офлайне»
    addToOfflineQueue({ text: 'queued 1' });
    addToOfflineQueue({ text: 'queued 2' });
    expect(getQueueSize()).toBe(2);

    const store = createTestStore();
    nextSocketConnected = true; // сокет будет подключён с самого старта
    const mounted = mountProvider(store);
    await act(async () => {});
    await act(async () => {});

    const socket = wsInstances[0];
    // Flush на маунте отправил накопленные сообщения прямо в сокет
    expect(socket.sentMessages.map((m) => m.text)).toEqual(['queued 1', 'queued 2']);
    // Провайдер добавил room в payload
    expect(socket.sentMessages[0].room).toBe('global');
    // Очередь пуста
    expect(getQueueSize()).toBe(0);

    mounted.unmount();
  });

  it('после подключения новая отправка идёт напрямую, минуя очередь', async () => {
    const store = createTestStore();
    const mounted = mountProvider(store);
    await act(async () => {});
    await act(async () => {});
    mounted.rerender(buildTree(store));

    const socket = wsInstances[0];
    socket.connected = true;

    let result;
    act(() => {
      result = sendFn({ text: 'online msg' });
    });

    expect(result).toBe(true);
    expect(socket.sentMessages).toHaveLength(1);
    expect(socket.sentMessages[0].text).toBe('online msg');
    expect(socket.sentMessages[0].room).toBe('global');
    expect(getQueueSize()).toBe(0);
  });
});