// NOTE: test → app import is acceptable for integration tests
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import { render, act } from '@testing-library/react';
import { Provider } from 'react-redux';

// Мокаем ТОЛЬКО axios-транспорт — usePresenceSync работает с реальным RTK Query
vi.mock('../../../shared/api/axiosInstance', () => ({
  chatApiInstance: vi.fn(async () => ({ data: { objects: [], count: 0 } })),
  characterApiInstance: vi.fn(async () => ({ data: [] })),
}));

import { chatApi } from '../../../entities/chat/api/chatApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { usePresenceSync } from '../../../app/providers/hooks/usePresenceSync';
import { chatApiInstance, characterApiInstance } from '../../../shared/api/axiosInstance';

const GLOBAL_ARGS = { locationSlug: null, limit: 50, offset: 0 };
const FOREST_ARGS = { locationSlug: 'forest', limit: 50, offset: 0 };
const TAVERN_ARGS = { locationSlug: 'tavern', limit: 50, offset: 0 };
const MY_ID = 999;

const selectOnline = (store, args) =>
  chatApi.endpoints.getOnlineCharacters.select(args)(store.getState()).data;
const selectStats = (store) =>
  characterApi.endpoints.getLocationsStats.select()(store.getState()).data;

const createTestStore = () =>
  configureStore({
    reducer: {
      [chatApi.reducerPath]: chatApi.reducer,
      [characterApi.reducerPath]: characterApi.reducer,
      local: () => ({ activeCharacterId: MY_ID }),
    },
    middleware: (getDefault) => getDefault().concat(chatApi.middleware, characterApi.middleware),
  });

const seedCaches = async (store) => {
  chatApiInstance.mockImplementation(async ({ url, params }) => {
    if (url === '/characters-online') {
      if (params?.location_slug === 'forest') {
        return { data: { objects: [{ id: 10, name: 'Alice', location_slug: 'forest' }], count: 1 } };
      }
      if (params?.location_slug === 'tavern') {
        return { data: { objects: [], count: 0 } };
      }
      return {
        data: {
          objects: [
            { id: 10, name: 'Alice', location_slug: 'forest' },
            { id: 20, name: 'Bob', location_slug: 'tavern' },
          ],
          count: 2,
        },
      };
    }
    return { data: { objects: [], count: 0 } };
  });
  characterApiInstance.mockImplementation(async () => ({
    data: [
      { location_slug: 'forest', count: 1 },
      { location_slug: 'tavern', count: 0 },
    ],
  }));

  await store.dispatch(chatApi.endpoints.getOnlineCharacters.initiate(GLOBAL_ARGS));
  await store.dispatch(chatApi.endpoints.getOnlineCharacters.initiate(FOREST_ARGS));
  await store.dispatch(chatApi.endpoints.getOnlineCharacters.initiate(TAVERN_ARGS));
  await store.dispatch(characterApi.endpoints.getLocationsStats.initiate());
};

const dispatchPresence = (detail) =>
  window.dispatchEvent(new CustomEvent('presence-event', { detail }));

const mountPresenceSync = (store) => {
  const TestComp = () => {
    usePresenceSync();
    return null;
  };
  return render(
    React.createElement(Provider, { store }, React.createElement(TestComp))
  );
};

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  document.body.innerHTML = '';
});

describe('Integration: usePresenceSync', () => {
  it('character_online увеличивает счётчик локации и добавляет пользователя в списки', async () => {
    const store = createTestStore();
    await seedCaches(store);
    mountPresenceSync(store);

    act(() => {
      dispatchPresence({
        event_type: 'character_online',
        character_id: 30,
        is_online: true,
        location_slug: 'tavern',
        user_data: { id: 30, name: 'Carol', location_slug: 'tavern' },
      });
    });

    // В глобальном списке стало 3 пользователя
    expect(selectOnline(store, GLOBAL_ARGS).count).toBe(3);
    // В локации tavern — 1 (был 0)
    const tavern = selectOnline(store, TAVERN_ARGS);
    expect(tavern.count).toBe(1);
    expect(tavern.objects[0].id).toBe(30);
    // Статистика: tavern +1, forest без изменений
    expect(selectStats(store)).toEqual(
      expect.arrayContaining([
        { location_slug: 'forest', count: 1 },
        { location_slug: 'tavern', count: 1 },
      ])
    );
  });

  it('character_location переносит пользователя: старая локация -1, новая +1', async () => {
    const store = createTestStore();
    await seedCaches(store);
    mountPresenceSync(store);

    act(() => {
      dispatchPresence({
        event_type: 'character_location',
        character_id: 10,
        old_location_slug: 'forest',
        new_location_slug: 'tavern',
        user_data: { id: 10, name: 'Alice', location_slug: 'tavern' },
      });
    });

    // forest: Alice удалена, счётчик 0
    const forest = selectOnline(store, FOREST_ARGS);
    expect(forest.objects).toHaveLength(0);
    expect(forest.count).toBe(0);
    // tavern: Alice добавлена, счётчик 1
    const tavern = selectOnline(store, TAVERN_ARGS);
    expect(tavern.objects).toHaveLength(1);
    expect(tavern.objects[0].id).toBe(10);
    expect(tavern.objects[0].location_slug).toBe('tavern');
    // В глобальном списке Alice осталась, но локация обновилась
    const global = selectOnline(store, GLOBAL_ARGS);
    expect(global.count).toBe(2);
    expect(global.objects.find((u) => u.id === 10).location_slug).toBe('tavern');
    // Статистика: forest -1, tavern +1
    expect(selectStats(store)).toEqual(
      expect.arrayContaining([
        { location_slug: 'forest', count: 0 },
        { location_slug: 'tavern', count: 1 },
      ])
    );
  });

  it('событие о собственном персонаже игнорируется (character_id === myCharacterId)', async () => {
    const store = createTestStore();
    await seedCaches(store);
    mountPresenceSync(store);

    const globalBefore = selectOnline(store, GLOBAL_ARGS);
    const forestBefore = selectOnline(store, FOREST_ARGS);
    const statsBefore = selectStats(store);

    act(() => {
      dispatchPresence({
        event_type: 'character_location',
        character_id: MY_ID, // === activeCharacterId из state.local
        old_location_slug: 'forest',
        new_location_slug: 'tavern',
        user_data: { id: MY_ID, name: 'Me' },
      });
    });

    // Состояние кэшей не изменилось вообще
    expect(selectOnline(store, GLOBAL_ARGS)).toBe(globalBefore);
    expect(selectOnline(store, FOREST_ARGS)).toBe(forestBefore);
    expect(selectStats(store)).toBe(statsBefore);
  });
});