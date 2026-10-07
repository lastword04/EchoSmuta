import { createApi } from '@reduxjs/toolkit/query/react';
import { statsApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const characterStatsApi = createApi({
  reducerPath: 'characterStatsApi',
  baseQuery: createAxiosBaseQuery(statsApiInstance),
  tagTypes: ['Buffs'],
  endpoints: (builder) => ({
    getCharacterBuffs: builder.query({
      query: (characterId) => ({ url: `/${characterId}/buffs`, method: 'GET' }),
      providesTags: ['Buffs'],
      transformResponse: (response) => response?.buffs || [],
    }),
  }),
});

export const { useGetCharacterBuffsQuery } = characterStatsApi;