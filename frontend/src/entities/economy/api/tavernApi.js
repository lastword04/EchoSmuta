import { createApi } from '@reduxjs/toolkit/query/react';
import { economyApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';
import { characterApi } from '../../character/api/characterApi';

export const tavernApi = createApi({
  reducerPath: 'tavernApi',
  baseQuery: createAxiosBaseQuery(economyApiInstance),
  tagTypes: ['Tavern'],
  endpoints: (builder) => ({
    getMeals: builder.query({
      query: () => ({ url: '/tavern/meals', method: 'GET' }),
      providesTags: ['Tavern'],
      keepUnusedDataFor: 5 * 60,
    }),

    buyMeal: builder.mutation({
      query: (mealId) => ({
        url: '/tavern/buy',
        method: 'POST',
        data: { meal_id: mealId },
      }),
      invalidatesTags: ['Tavern'],
      // Межслайсовая инвалидация: теги RTK не пересекают границы api-слайсов,
      // поэтому Character инвалидируем прямым dispatch в api-слое, в одном месте
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),
  }),
});

export const { useGetMealsQuery, useBuyMealMutation } = tavernApi;