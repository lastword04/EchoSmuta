import { createApi } from '@reduxjs/toolkit/query/react';
import { economyApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';
import { characterApi } from '../../character/api/characterApi';
import { resourcesApi } from '../../resources/api/resourcesApi'; 

export const economyApi = createApi({
  reducerPath: 'economyApi',
  baseQuery: createAxiosBaseQuery(economyApiInstance),
  tagTypes: ['Economy'],
  endpoints: (builder) => ({
    // ═══ QUERIES (read-only) ═══
    getResources: builder.query({
      query: () => ({ url: '/buyout/resources', method: 'GET' }),
      providesTags: ['Economy'],
      keepUnusedDataFor: 5 * 60,
    }),

    getLots: builder.query({
      query: () => ({ url: '/exchange/lots', method: 'GET' }),
      providesTags: ['Economy'],
      keepUnusedDataFor: 5 * 60,
    }),

    // ═══ СКУПКА (мутации → дукаты + ресурсы) ═══
    buyResource: builder.mutation({
      query: ({ resource_id, quantity }) => ({
        url: '/buyout/buy',
        method: 'POST',
        data: { resource_id, quantity },
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),

    sellResource: builder.mutation({
      query: ({ resource_id, quantity }) => ({
        url: '/buyout/sell',
        method: 'POST',
        data: { resource_id, quantity },
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),

    buyResourcesBulk: builder.mutation({
      query: (items) => ({
        url: '/buyout/buy-bulk',
        method: 'POST',
        data: { items }, 
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),

    sellResourcesBulk: builder.mutation({
      query: (items) => ({
        url: '/buyout/sell-bulk',
        method: 'POST',
        data: { items },
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),

    // ═══ БИРЖА (мутации → дукаты + ресурсы) ═══
    createLot: builder.mutation({
      query: (data) => ({
        url: '/exchange/lots',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),

    dealLot: builder.mutation({
      query: ({ lotId, quantity }) => ({
        url: `/exchange/lots/${lotId}/deal`,
        method: 'POST',
        data: quantity != null ? { quantity } : {},
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),

    cancelLot: builder.mutation({
      query: (lotId) => ({
        url: `/exchange/lots/${lotId}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: ['Economy'],
      async onQueryStarted(arg, { queryFulfilled, dispatch }) {
        try {
          await queryFulfilled;
          dispatch(characterApi.util.invalidateTags(['Character']));
          dispatch(resourcesApi.util.invalidateTags(['Resources']));
        } catch {
          // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
        }
      },
    }),
  }),
});

export const {
  useGetResourcesQuery,
  useGetLotsQuery,
  useBuyResourceMutation,
  useSellResourceMutation,
  useBuyResourcesBulkMutation,
  useSellResourcesBulkMutation,
  useCreateLotMutation,
  useDealLotMutation,
  useCancelLotMutation,
} = economyApi;