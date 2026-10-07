import { createApi } from '@reduxjs/toolkit/query/react';
import { notebookApiInstance } from '../../../shared/api/axiosInstance'; // Проверь путь!
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery'; // Проверь путь!

export const notebookApi = createApi({
  reducerPath: 'notebookApi',
  baseQuery: createAxiosBaseQuery(notebookApiInstance),
  tagTypes: ['Notebook'],
  endpoints: (builder) => ({
    // GET /api/notebook/my
    getMyNotebook: builder.query({
      query: () => ({ url: '/my', method: 'GET' }),
      providesTags: ['Notebook'],
    }),

    // PUT /api/notebook/{notebook_id}
    updateNotebook: builder.mutation({
      query: ({ notebookId, data }) => ({
        url: `/${notebookId}`,
        method: 'PUT',
        data, // Тело запроса: { text: "..." }
      }),
      invalidatesTags: ['Notebook'], // Автоматически обновит кэш getMyNotebook при успехе
    }),
  }),
});

export const {
  useGetMyNotebookQuery,
  useUpdateNotebookMutation,
} = notebookApi;