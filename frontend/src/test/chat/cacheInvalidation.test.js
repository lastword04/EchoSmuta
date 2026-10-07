import { describe, it, expect, vi, beforeEach } from 'vitest';

// Мокаем chatApi, чтобы не поднимать настоящий RTK Query API и не ходить в сеть
vi.mock('../../entities/chat/api/chatApi', () => ({
  chatApi: {
    util: {
      invalidateTags: vi.fn((tags) => ({ type: 'invalidateTags', tags })),
      updateQueryData: vi.fn(),
    },
  },
}));

import { invalidateChatCache } from '../../entities/chat/lib/cacheInvalidation';
import { chatApi } from '../../entities/chat/api/chatApi';

const getDispatchedTags = () => chatApi.util.invalidateTags.mock.calls.at(-1)?.[0];

beforeEach(() => {
  chatApi.util.invalidateTags.mockClear();
});

describe('invalidateChatCache', () => {
  it("{ history: true } без historyRoom — инвалидирует 'ChatHistory' (всю историю)", () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { history: true });

    expect(chatApi.util.invalidateTags).toHaveBeenCalledTimes(1);
    expect(getDispatchedTags()).toEqual(['ChatHistory']);
    expect(dispatch).toHaveBeenCalledTimes(1);
  });

  it("{ history: true, historyRoom: 'global' } — инвалидирует { type: 'ChatHistory', id: 'global' }", () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { history: true, historyRoom: 'global' });

    expect(getDispatchedTags()).toEqual([{ type: 'ChatHistory', id: 'global' }]);
  });

  it("{ history: true, historyRoom: 'location:forest' } — инвалидирует { type: 'ChatHistory', id: 'location:forest' }", () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { history: true, historyRoom: 'location:forest' });

    expect(getDispatchedTags()).toEqual([{ type: 'ChatHistory', id: 'location:forest' }]);
  });

  it('{ onlineUsers: true } — инвалидирует { type: OnlineUsers, id: global }', () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { onlineUsers: true });

    expect(getDispatchedTags()).toEqual([{ type: 'OnlineUsers', id: 'global' }]);
  });

  it("{ onlineUsers: true, locations: ['forest', 'tavern'] } — добавляет локации к тегам", () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { onlineUsers: true, locations: ['forest', 'tavern'] });

    expect(getDispatchedTags()).toEqual([
      { type: 'OnlineUsers', id: 'global' },
      { type: 'OnlineUsers', id: 'forest' },
      { type: 'OnlineUsers', id: 'tavern' },
    ]);
  });

  it('{ history: true, onlineUsers: true } — комбинирует оба типа тегов', () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { history: true, onlineUsers: true });

    expect(getDispatchedTags()).toEqual([
      'ChatHistory',
      { type: 'OnlineUsers', id: 'global' },
    ]);
    // Одна пачка тегов — один dispatch
    expect(dispatch).toHaveBeenCalledTimes(1);
  });

  it('пустой options {} — ничего не вызывает dispatch', () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, {});

    expect(chatApi.util.invalidateTags).not.toHaveBeenCalled();
    expect(dispatch).not.toHaveBeenCalled();
  });

  it('dispatch не вызывается если tags пустой (options по умолчанию)', () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch);

    expect(chatApi.util.invalidateTags).not.toHaveBeenCalled();
    expect(dispatch).not.toHaveBeenCalled();
  });

  it('locations: [] (пустой массив) — не добавляет лишних тегов', () => {
    const dispatch = vi.fn();
    invalidateChatCache(dispatch, { onlineUsers: true, locations: [] });

    expect(getDispatchedTags()).toEqual([{ type: 'OnlineUsers', id: 'global' }]);
  });
});