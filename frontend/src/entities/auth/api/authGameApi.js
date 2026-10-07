import { createApi } from '@reduxjs/toolkit/query/react';
import { authProtectedApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const authGameApi = createApi({
  reducerPath: 'authGameApi',
  baseQuery: createAxiosBaseQuery(authProtectedApiInstance),
  endpoints: (builder) => ({
    play: builder.mutation({
      query: ({ characterId, data }) => ({
        url: `/characters/${characterId}/play`,
        method: 'POST',
        data,
      }),
    }),

    playMain: builder.mutation({
      query: (data) => ({
        url: '/characters/main/play',
        method: 'POST',
        data,
      }),
    }),

    quit: builder.mutation({
      query: ({ characterId, data }) => ({
        url: `/characters/${characterId}/quit`,
        method: 'POST',
        data,
      }),
    }),
  }),
});

export const {
  usePlayMutation,
  usePlayMainMutation,
  useQuitMutation,
} = authGameApi;