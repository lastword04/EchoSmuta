import { createApi } from '@reduxjs/toolkit/query/react';
import { panelApiInstance } from '../../../shared/api/axiosInstance'; // Проверь путь
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery'; // Проверь путь

export const panelApi = createApi({
  reducerPath: 'panelApi',
  baseQuery: createAxiosBaseQuery(panelApiInstance),
  tagTypes: ['Panel'],
  endpoints: (builder) => ({
    getMyPanels: builder.query({
      query: () => ({ url: '/my', method: 'GET' }),
      providesTags: ['Panel'],
    }),
    updatePanel: builder.mutation({
      query: ({ panelId, data }) => ({
        url: `/${panelId}`,
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['Panel'],
    }),
  }),
});

export const {
  useGetMyPanelsQuery,
  useUpdatePanelMutation,
} = panelApi;