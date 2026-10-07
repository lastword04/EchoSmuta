import { createApi } from '@reduxjs/toolkit/query/react';
import { forumApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const forumApi = createApi({
  reducerPath: 'forumApi',
  baseQuery: createAxiosBaseQuery(forumApiInstance),
  tagTypes: ['Forums', 'Topics'],
  endpoints: (builder) => ({
    getAllForums: builder.query({
      query: () => ({
        url: '/',
        method: 'GET',
      }),
      providesTags: ['Forums'],
    }),

    getForumTopics: builder.query({
      query: ({ forumId, limit = 10, offset = 0 }) => ({
        url: `/${forumId}/topics`,
        method: 'GET',
        params: { limit, offset },
      }),
      providesTags: (result, error, { forumId }) =>
        result ? [{ type: 'Topics', id: forumId }] : [],
    }),

    checkForumAuth: builder.query({
      query: () => ({
        url: '/auth',
        method: 'HEAD',
        skipAuthRetry: true, // 401 не запускает refresh-цепочку
      }),
      // Если HEAD не упал — значит статус 204, авторизация есть
      transformResponse: () => true,
    }),

    createTopic: builder.mutation({
      query: ({ forumId, topicData }) => ({
        url: `/${forumId}/topics`,
        method: 'POST',
        data: topicData,
      }),
      invalidatesTags: (result, error, { forumId }) => [
        { type: 'Topics', id: forumId },
        'Forums',
      ],
    }),

    createTopicWithComment: builder.mutation({
      query: ({ forumId, requestData }) => ({
        url: `/${forumId}/topics-comment`,
        method: 'POST',
        data: requestData,
      }),
      invalidatesTags: (result, error, { forumId }) => [
        { type: 'Topics', id: forumId },
        'Forums',
      ],
    }),
  }),
});

export const {
  useGetAllForumsQuery,
  useGetForumTopicsQuery,
  useCheckForumAuthQuery,
  useLazyCheckForumAuthQuery,
  useCreateTopicMutation,
  useCreateTopicWithCommentMutation,
} = forumApi;