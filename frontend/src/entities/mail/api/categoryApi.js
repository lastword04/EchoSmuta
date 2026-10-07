import { createApi } from '@reduxjs/toolkit/query/react';
import { categoryApiInstance } from '../../../shared/api/axiosInstance'; // Проверь путь!
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery'; // Проверь путь!

export const categoryApi = createApi({
  reducerPath: 'categoryApi',
  baseQuery: createAxiosBaseQuery(categoryApiInstance),
  tagTypes: ['Category', 'CategoryDetails', 'CategoryCharacters'],
  endpoints: (builder) => ({
    // 1. GET /api/categories/
    getMyCategories: builder.query({
      query: () => ({ url: '/', method: 'GET' }),
      providesTags: ['Category'],
    }),

    // 2. GET /api/categories/detail
    getCategoryDetails: builder.query({
      query: () => ({ url: '/detail', method: 'GET' }),
      providesTags: ['CategoryDetails'],
    }),

    // 3. GET /api/categories/{category_id}?is_online=true/false
    getCategoryCharacters: builder.query({
      query: ({ categoryId, isOnline }) => ({
        url: `/${categoryId}`,
        method: 'GET',
        // Передаем параметр только если он не null/undefined
        params: isOnline !== null && isOnline !== undefined ? { is_online: isOnline } : undefined,
      }),
      providesTags: (result, error, { categoryId }) => [
        { type: 'CategoryCharacters', id: categoryId }
      ],
    }),

    // 4. POST /api/categories/
    createCategory: builder.mutation({
      query: (data) => ({ 
        url: '/', 
        method: 'POST', 
        data // Тело запроса: { name: "..." }
      }),
      invalidatesTags: ['Category', 'CategoryDetails'],
    }),

    // 5. DELETE /api/categories/{category_id}
    deleteCategory: builder.mutation({
      query: (categoryId) => ({ 
        url: `/${categoryId}`, 
        method: 'DELETE' 
      }),
      invalidatesTags: ['Category', 'CategoryDetails'],
    }),

    // 6. POST /api/categories/{category_id}/characters/{character_name}
    addCharacter: builder.mutation({
      query: ({ categoryId, characterName }) => ({
        url: `/${categoryId}/characters/${characterName}`,
        method: 'POST',
      }),     
      invalidatesTags: ['CategoryDetails', 'CategoryCharacters'], 
    }),

    // 7. DELETE /api/categories/{category_id}/characters/{character_id}
    removeCharacter: builder.mutation({
      query: ({ categoryId, characterId }) => ({
        url: `/${categoryId}/characters/${characterId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['CategoryDetails', 'CategoryCharacters'],
    }),

    // 8. PUT /api/categories/{category_id}
    updateCategoryCheckboxes: builder.mutation({
      query: ({ categoryId, data }) => ({
        url: `/${categoryId}`,
        method: 'PUT',
        data, // Тело запроса: { is_send_notifications: true, ... }
      }),
      invalidatesTags: ['CategoryDetails'],
    }),
  }),
});

export const {
  useGetMyCategoriesQuery,
  useGetCategoryDetailsQuery,
  useGetCategoryCharactersQuery,
  useCreateCategoryMutation,
  useDeleteCategoryMutation,
  useAddCharacterMutation,
  useRemoveCharacterMutation,
  useUpdateCategoryCheckboxesMutation,
} = categoryApi;