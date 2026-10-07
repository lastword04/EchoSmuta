import { createApi } from '@reduxjs/toolkit/query/react';
import { forumApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const commentApi = createApi({
  reducerPath: 'commentApi',
  baseQuery: createAxiosBaseQuery(forumApiInstance),
  tagTypes: ['Comments'],
  endpoints: (builder) => ({
    getTopicComments: builder.query({
      query: ({ forumId, topicId, limit = 10, offset = 0 }) => ({
        url: `/${forumId}/topics/${topicId}/comments`,
        method: 'GET',
        params: { limit, offset },
      }),
      providesTags: (result, error, { topicId }) =>
        result ? [{ type: 'Comments', id: topicId }] : [],
    }),

    createComment: builder.mutation({
      query: ({ forumId, topicId, commentData }) => ({
        url: `/${forumId}/topics/${topicId}/comments`,
        method: 'POST',
        data: commentData,
      }),
      invalidatesTags: (result, error, { topicId }) => [
        { type: 'Comments', id: topicId },
      ],
    }),

    trackTopicActivity: builder.mutation({
      query: ({ forumId, topicId }) => ({
        url: `/${forumId}/topics/${topicId}/activity`,
        method: 'POST',
      }),
      // 204 = активность зарегистрирована
      transformResponse: () => true,
    }),
  }),
});

export const {
  useGetTopicCommentsQuery,
  useCreateCommentMutation,
  useTrackTopicActivityMutation,
} = commentApi;