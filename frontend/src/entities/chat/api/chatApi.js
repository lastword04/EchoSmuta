import { createApi } from '@reduxjs/toolkit/query/react';
import { chatApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';

export const chatApi = createApi({
  reducerPath: 'chatApi',
  baseQuery: createAxiosBaseQuery(chatApiInstance),
  tagTypes: ['ChatSettings', 'ChatHistory', 'OnlineUsers'],
  endpoints: (builder) => ({
    // ═══ QUERIES ═══
    getMySettings: builder.query({
      query: () => ({
        url: '/settings/',
        method: 'GET',
      }),
      providesTags: ['ChatSettings'],
      keepUnusedDataFor: 300,
    }),

    getChatHistory: builder.query({
      query: ({ room, limit = 50, offset = 0, roomId = null }) => ({
        url: `/${room}/history`,
        method: 'GET',
        params: {
          limit,
          offset,
          // На бэке параметр называется location_slug — оставляем это имя
          // в query для совместимости, но на фронте он означает «комната»:
          // может быть и локацией, и 'house:uuid', и 'inn:inside'.
          ...(roomId && { location_slug: roomId }),
        },
      }),
      providesTags: (result, error, { room, roomId }) => {
        const roomKey = room === 'global' && roomId
          ? `location:${roomId}`
          : room;
        return [{ type: 'ChatHistory', id: roomKey }];
      },
      keepUnusedDataFor: 300,
      keepPreviousData: true,
      transformResponse: (response) => {
        // Форматируем сообщения на уровне API (единая точка)
        return (response.objects || []).map(msg => ({
          id: msg.id,
          time: msg.created_at
            ? parseUtcDate(msg.created_at).toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit',
              })
            : '',
          user: msg.sender_name,
          user_id: msg.sender_id,
          text: msg.content,
          message_type: msg.message_type,
          room: msg.room,
          is_trade: msg.is_trade,
          target_user_ids: msg.target_user_ids || [],
          target_user_names: msg.target_user_names || [],
        }));
      },
    }),

    getOnlineCharacters: builder.query({
      query: ({ roomId = null, locationSlug = null, limit = 50, offset = 0 }) => ({
        url: '/characters-online',
        method: 'GET',
        params: {
          limit,
          offset,
          ...(locationSlug && { location_slug: locationSlug }),
          ...(roomId && { room_id: roomId }),
        },
      }),
      providesTags: (result, error, { roomId, locationSlug }) => {
        const key = roomId || locationSlug || 'global';
        return [{ type: 'OnlineUsers', id: key }];
      },
      keepUnusedDataFor: 300,
      transformResponse: (response) => ({
        objects: response.objects || [],
        count: response.count || 0,
      }),
    }),

    // ═══ MUTATIONS ═══
    updateMySettings: builder.mutation({
      query: ({ settingsId, data }) => ({
        url: `/settings/${settingsId}`,
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['ChatSettings'],
    }),

    addToIgnore: builder.mutation({
      query: (data) => ({
        url: '/ignore',
        method: 'POST',
        data,
      }),
    }),

    deleteFromIgnore: builder.mutation({
      query: (ignoredCharacterId) => ({
        url: `/ignore/${ignoredCharacterId}`,
        method: 'DELETE',
      }),
    }),
  }),
});

export const {
  useGetMySettingsQuery,
  useGetChatHistoryQuery,
  useGetOnlineCharactersQuery,
  useUpdateMySettingsMutation,
  useAddToIgnoreMutation,
  useDeleteFromIgnoreMutation,
} = chatApi;



// ═══ Единый строитель аргументов истории чата ═══
// ВСЕ обращения к getChatHistory (запрос, префетчи, updateQueryData) обязаны
// строить аргументы только через эту функцию: RTK сравнивает ключи байт-в-байт,
// разный порядок полей = разные ячейки кэша = двойные запросы.
//
// roomId — виртуальная комната/локация ('1.19.residential-area', 'house:uuid',
// 'inn:inside'). Null — глобальный чат без локационного фильтра.
export const chatHistoryArgs = (room, roomId = null) => ({
  room,
  limit: 50,
  offset: 0,
  roomId: roomId ?? null,
});

// Хелпер для обновления истории из WebSocket
export const addMessageToChatHistory = (dispatch, { room, roomId, message }) => {
  const rId = roomId || null;
  const args = chatHistoryArgs(room, rId);
  dispatch(
    chatApi.util.updateQueryData(
      'getChatHistory',
      args,
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