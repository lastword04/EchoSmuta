import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';

// Мокаем ТОЛЬКО axios-транспорт: реальный chatApi (createApi) работает как в проде
vi.mock('../../../shared/api/axiosInstance', () => ({
  chatApiInstance: vi.fn(async () => ({ data: { objects: [] } })),
  characterApiInstance: vi.fn(async () => ({ data: {} })),
}));

import { chatApi, addMessageToChatHistory } from '../../../entities/chat/api/chatApi';
import { invalidateChatCache } from '../../../entities/chat/lib/cacheInvalidation';
import { chatApiInstance as chatApiInstanceMock } from '../../../shared/api/axiosInstance';

const createTestStore = () =>
  configureStore({
    reducer: { [chatApi.reducerPath]: chatApi.reducer },
    middleware: (getDefault) => getDefault().concat(chatApi.middleware),
  });

const HISTORY_ARGS = { room: 'global', limit: 50, offset: 0, locationSlug: null };

const loadHistory = async (store) => {
  const promise = store.dispatch(
    chatApi.endpoints.getChatHistory.initiate(HISTORY_ARGS)
  );
  const { data } = await promise;
  return data;
};

const selectHistory = (store) =>
  chatApi.endpoints.getChatHistory.select(HISTORY_ARGS)(store.getState()).data;

const findHistoryEntry = (store, locationSlug) =>
  Object.values(store.getState().chatApi.queries).find(
    (q) => q.endpointName === 'getChatHistory' && (q.originalArgs?.locationSlug ?? null) === locationSlug
  );

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Integration: addMessageToChatHistory + cacheInvalidation', () => {
  it('сообщение через WebSocket попадает в кэш getChatHistory поверх данных с сервера', async () => {
    // Сервер отдал историю с одним сообщением
    chatApiInstanceMock.mockResolvedValueOnce({
      data: {
        objects: [
          { id: 1, created_at: '2026-09-10T12:30:00Z', sender_name: 'Alice', sender_id: 10, content: 'привет' },
        ],
      },
    });

    const store = createTestStore();
    const data = await loadHistory(store);

    // transformResponse отработал на реальном эндпоинте
    expect(data).toHaveLength(1);
    expect(data[0].user).toBe('Alice');
    expect(data[0].text).toBe('привет');
    expect(selectHistory(store)).toHaveLength(1);

    // WebSocket-сообщение через хелпер дописывается в тот же кэш
    addMessageToChatHistory(store.dispatch, {
      room: 'global',
      locationSlug: null,
      message: { id: 2, text: 'из ws', user: 'Bob' },
    });

    const cached = selectHistory(store);
    expect(cached).toHaveLength(2);
    expect(cached.map((m) => m.id)).toEqual([1, 2]);
  });

  it('invalidateChatCache помечает запись getChatHistory инвалидированной — кэш и WebSocket-апдейт консистентны', async () => {
    chatApiInstanceMock.mockResolvedValue({
      data: { objects: [{ id: 1, created_at: '2026-09-10T12:30:00Z', sender_name: 'Alice', sender_id: 10, content: 'привет' }] },
    });

    const store = createTestStore();
    await loadHistory(store);
    addMessageToChatHistory(store.dispatch, {
      room: 'global',
      locationSlug: null,
      message: { id: 2, text: 'ws' },
    });
    expect(selectHistory(store)).toHaveLength(2);

    // До инвалидации запись загружена, сеть дергалась один раз
    expect(findHistoryEntry(store, null).status).toBe('fulfilled');
    const callsBefore = chatApiInstanceMock.mock.calls.length;
    expect(callsBefore).toBe(1);

    invalidateChatCache(store.dispatch, { history: true, historyRoom: 'global' });

    // Сразу после инвалидации: кэш НЕ очищен (данные остаются до refetch)
    expect(selectHistory(store)).toHaveLength(2);

    // Refetch запустился и завершился — сеть дернулась второй раз
    await flushPromises();
    expect(chatApiInstanceMock.mock.calls.length).toBe(callsBefore + 1);
    expect(findHistoryEntry(store, null).status).toBe('fulfilled');

    // После refetch кэш = каноничный снапшот сервера (ws-оптимистичный апдейт перезаписан)
    const after = selectHistory(store);
    expect(after).toHaveLength(1);
    expect(after[0].id).toBe(1);
  });

  it('инвалидация конкретной комнаты не трогает кэш другой комнаты', async () => {
    // Ответ зависит от location_slug в params — refetch возвращает консистентные данные
    chatApiInstanceMock.mockImplementation(async ({ params }) => ({
      data: { objects: [{ id: params?.location_slug === 'forest' ? 100 : 1 }] },
    }));

    const store = createTestStore();
    await store.dispatch(chatApi.endpoints.getChatHistory.initiate(HISTORY_ARGS));
    const locationArgs = { room: 'global', limit: 50, offset: 0, locationSlug: 'forest' };
    await store.dispatch(chatApi.endpoints.getChatHistory.initiate(locationArgs));

    const callsBefore = chatApiInstanceMock.mock.calls.length;
    expect(findHistoryEntry(store, null).status).toBe('fulfilled');
    expect(findHistoryEntry(store, 'forest').status).toBe('fulfilled');

    invalidateChatCache(store.dispatch, { history: true, historyRoom: 'global' });

    // Синхронно: refetch ушёл только у 'global', запись 'forest' не тронута
    expect(findHistoryEntry(store, null).status).toBe('pending');
    expect(findHistoryEntry(store, 'forest').status).toBe('fulfilled');

    await flushPromises();
    // Ровно один дополнительный запрос — только инвалидированная комната
    expect(chatApiInstanceMock.mock.calls.length).toBe(callsBefore + 1);
    expect(findHistoryEntry(store, 'forest').status).toBe('fulfilled');
  });
});