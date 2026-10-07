import { createApi } from '@reduxjs/toolkit/query/react';
import { currencyApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const currencyApi = createApi({
  reducerPath: 'currencyApi',
  baseQuery: createAxiosBaseQuery(currencyApiInstance),
  tagTypes: ['ExchangeSettings', 'Lots'],
  endpoints: (builder) => ({
    
    getExchangeSettings: builder.query({
    query: () => ({
        url: '/settings',
        method: 'GET',
    }),
    providesTags: ['ExchangeSettings'],
    }),

    getLots: builder.query({
    query: ({ buyFor, limit, offset }) => ({
        url: '/',
        method: 'GET',
        params: { buy_for: buyFor, limit, offset },
    }),
    providesTags: ['Lots'],
    // Держим в кэше всего 30 сек — биржа часто меняется
    keepUnusedDataFor: 30,
    }),

    createLot: builder.mutation({
    query: (lotData) => ({
        url: '/',
        method: 'POST',
        data: lotData,
    }),
    // MyCharacters инвалидируем в characterApi, но тут это отдельный API,
    // поэтому добавим кастомную инвалидацию ниже
    invalidatesTags: ['Lots'],
    }),

    buyLot: builder.mutation({
    query: (lotId) => ({
        url: `/${lotId}/buy`,
        method: 'POST',
    }),
    invalidatesTags: ['Lots'],
    }),

    deleteLot: builder.mutation({
    query: (lotId) => ({
        url: `/${lotId}`,
        method: 'DELETE',
    }),
    invalidatesTags: ['Lots'],
    }),
  }),
});

export const {
  useGetExchangeSettingsQuery,
  useGetLotsQuery,
  useCreateLotMutation,
  useBuyLotMutation,
  useDeleteLotMutation,
} = currencyApi;