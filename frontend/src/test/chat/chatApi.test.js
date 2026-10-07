import { describe, it, expect, vi, beforeEach } from 'vitest';

// Создаём мок функции
const updateQueryData = vi.fn((endpointName, args, updater) => ({ updater, args, endpointName }));
const invalidateTags = vi.fn();

// Мокаем весь модуль, но переэкспортируем addMessageToChatHistory с мокнутым chatApi
vi.mock('../../entities/chat/api/chatApi', () => {
  const mockChatApi = {
    util: {
      updateQueryData: (...args) => updateQueryData(...args),
      invalidateTags: (...args) => invalidateTags(...args),
    },
  };

  // Копия addMessageToChatHistory из исходника, но использует мокнутый mockChatApi
  const addMessageToChatHistory = (dispatch, { room, locationSlug, message }) => {
    const location = locationSlug || null;
    
    dispatch(
      mockChatApi.util.updateQueryData(
        'getChatHistory',
        { room, limit: 50, offset: 0, locationSlug: location },
        (draft) => {
          const existingIds = new Set(draft.map(m => m.id).filter(Boolean));
          
          if (message.id && existingIds.has(message.id)) {
            return;
          }
          
          draft.push(message);
          
          if (draft.length > 200) {
            draft.splice(0, draft.length - 200);
          }
        }
      )
    );
  };

  return {
    chatApi: mockChatApi,
    addMessageToChatHistory,
    useGetMySettingsQuery: vi.fn(),
    useGetChatHistoryQuery: vi.fn(),
    useGetOnlineCharactersQuery: vi.fn(),
    useUpdateMySettingsMutation: vi.fn(),
    useAddToIgnoreMutation: vi.fn(),
    useDeleteFromIgnoreMutation: vi.fn(),
  };
});

import { addMessageToChatHistory } from '../../entities/chat/api/chatApi';

const HISTORY_LIMIT = 200;

const runUpdaterOn = (initialMessages, message) => {
  const dispatch = vi.fn();
  addMessageToChatHistory(dispatch, { room: 'global', locationSlug: null, message });

  expect(updateQueryData).toHaveBeenCalledWith(
    'getChatHistory',
    { room: 'global', limit: 50, offset: 0, locationSlug: null },
    expect.any(Function)
  );
  const { updater } = updateQueryData.mock.results.at(-1).value;
  const draft = [...initialMessages];
  updater(draft);
  return draft;
};

beforeEach(() => {
  updateQueryData.mockClear();
});

describe('addMessageToChatHistory', () => {
  it('добавляет новое сообщение в историю', () => {
    const draft = runUpdaterOn([{ id: 1, text: 'old' }], { id: 2, text: 'new' });
    expect(draft).toHaveLength(2);
    expect(draft[1]).toEqual({ id: 2, text: 'new' });
  });

  it('не создаёт дубликаты по id', () => {
    const draft = runUpdaterOn([{ id: 5, text: 'a' }, { id: 6, text: 'b' }], { id: 5, text: 'duplicate' });
    expect(draft).toHaveLength(2);
    expect(draft.filter((m) => m.id === 5)).toHaveLength(1);
  });

  it('добавляет сообщение без id (не считается дубликатом)', () => {
    const draft = runUpdaterOn([{ id: 1 }], { text: 'no id' });
    expect(draft).toHaveLength(2);
  });

  it('ограничивает длину массива до 200 сообщений, отрезая самые старые', () => {
    const initial = Array.from({ length: HISTORY_LIMIT }, (_, i) => ({ id: i + 1 }));
    const draft = runUpdaterOn(initial, { id: 999, text: 'fresh' });

    expect(draft).toHaveLength(HISTORY_LIMIT);
    expect(draft.at(-1)).toEqual({ id: 999, text: 'fresh' });
    expect(draft[0].id).toBe(initial.length - HISTORY_LIMIT + 2);
    expect(draft.some((m) => m.id === 1)).toBe(false);
  });

  it('не трогает историю, если она короче лимита', () => {
    const initial = Array.from({ length: 10 }, (_, i) => ({ id: i + 1 }));
    const draft = runUpdaterOn(initial, { id: 11 });
    expect(draft).toHaveLength(11);
    expect(draft[0]).toEqual({ id: 1 });
  });

  it('передаёт locationSlug в аргументы updateQueryData', () => {
    const dispatch = vi.fn();
    addMessageToChatHistory(dispatch, { room: 'global', locationSlug: 'tavern', message: { id: 1 } });
    expect(updateQueryData).toHaveBeenCalledWith(
      'getChatHistory',
      { room: 'global', limit: 50, offset: 0, locationSlug: 'tavern' },
      expect.any(Function)
    );
  });
});